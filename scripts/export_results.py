#!/usr/bin/env python3
"""
Script CLI pour exporter les résultats d'un scan.
Phase 3.3 - Export en ligne de commande

Usage:
    python scripts/export_results.py --scan-id SCAN_ID --format csv --output export.csv
    python scripts/export_results.py --scan-id SCAN_ID --format json --output export.json
"""

import argparse
import sys
from pathlib import Path
import yaml
import logging

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseManager
from utils import setup_logging, format_size, format_timestamp
import pandas as pd
import json
from datetime import datetime


def export_csv(db, scan_id, output_path, filters=None):
    """
    Export données en CSV.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        output_path: Chemin fichier sortie
        filters: Filtres optionnels (non implémenté)
    """
    cursor = db.conn.cursor()
    
    query = """
        SELECT 
            path, name, extension, size_bytes, 
            owner_name, group_name, permissions, 
            mtime, atime
        FROM files
        WHERE scan_id = ?
        ORDER BY size_bytes DESC
    """
    
    cursor.execute(query, (scan_id,))
    
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    
    df = pd.DataFrame(data, columns=columns)
    
    # Formater colonnes
    df['size_formatted'] = df['size_bytes'].apply(format_size)
    df['mtime_formatted'] = df['mtime'].apply(format_timestamp)
    
    df.to_csv(output_path, index=False)
    
    print(f"✅ Export CSV réussi: {output_path}")
    print(f"   Lignes: {len(df):,}")
    print(f"   Colonnes: {len(df.columns)}")


def export_json(db, scan_id, output_path, filters=None):
    """
    Export données en JSON.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        output_path: Chemin fichier sortie
        filters: Filtres optionnels (non implémenté)
    """
    cursor = db.conn.cursor()
    
    # Informations scan
    cursor.execute("""
        SELECT scan_id, start_time, end_time, total_files, total_size_bytes
        FROM scans
        WHERE scan_id = ?
    """, (scan_id,))
    
    scan_row = cursor.fetchone()
    
    if not scan_row:
        print(f"❌ Scan introuvable: {scan_id}")
        sys.exit(1)
    
    scan_info = {
        'scan_id': scan_row[0],
        'start_time': scan_row[1],
        'end_time': scan_row[2],
        'total_files': scan_row[3],
        'total_size_bytes': scan_row[4]
    }
    
    # Fichiers (limiter à 50k pour JSON)
    cursor.execute("""
        SELECT path, name, extension, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ?
        ORDER BY size_bytes DESC
        LIMIT 50000
    """, (scan_id,))
    
    files = []
    for row in cursor.fetchall():
        files.append({
            'path': row[0],
            'name': row[1],
            'extension': row[2],
            'size_bytes': row[3],
            'owner': row[4],
            'mtime': row[5]
        })
    
    # Assembler export
    export_data = {
        'scan': scan_info,
        'files': files,
        'export_date': datetime.now().isoformat(),
        'files_count': len(files)
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Export JSON réussi: {output_path}")
    print(f"   Fichiers exportés: {len(files):,} (max 50k)")


def export_excel(db, scan_id, output_path, filters=None):
    """
    Export données en Excel.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        output_path: Chemin fichier sortie
        filters: Filtres optionnels (non implémenté)
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("❌ Module openpyxl non installé")
        print("   Installez avec: pip install openpyxl")
        sys.exit(1)
    
    cursor = db.conn.cursor()
    
    # Récupérer données fichiers
    cursor.execute("""
        SELECT 
            path, name, extension, size_bytes,
            owner_name, group_name, permissions, mtime
        FROM files
        WHERE scan_id = ?
        ORDER BY size_bytes DESC
        LIMIT 100000
    """, (scan_id,))
    
    columns = ['Chemin', 'Nom', 'Extension', 'Taille (bytes)', 
               'Propriétaire', 'Groupe', 'Permissions', 'Date modification']
    data = cursor.fetchall()
    
    df_files = pd.DataFrame(data, columns=columns)
    
    # Formater
    df_files['Taille'] = df_files['Taille (bytes)'].apply(format_size)
    df_files['Date'] = df_files['Date modification'].apply(format_timestamp)
    
    # Créer Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Feuille fichiers
        df_export = df_files[['Nom', 'Taille', 'Propriétaire', 'Date', 'Chemin']]
        df_export.to_excel(writer, sheet_name='Fichiers', index=False)
        
        # Feuille statistiques extensions
        cursor.execute("""
            SELECT 
                extension,
                COUNT(*) as count,
                SUM(size_bytes) as total_size
            FROM files
            WHERE scan_id = ?
            GROUP BY extension
            ORDER BY total_size DESC
            LIMIT 100
        """, (scan_id,))
        
        ext_data = cursor.fetchall()
        df_ext = pd.DataFrame(ext_data, columns=['Extension', 'Nombre', 'Taille (bytes)'])
        df_ext['Taille'] = df_ext['Taille (bytes)'].apply(format_size)
        df_ext.to_excel(writer, sheet_name='Extensions', index=False)
    
    print(f"✅ Export Excel réussi: {output_path}")
    print(f"   Lignes: {len(df_files):,} (max 100k)")


def list_scans(db):
    """
    Liste les scans disponibles.
    
    Args:
        db: DatabaseManager
    """
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT scan_id, start_time, total_files, total_size_bytes
        FROM scans
        ORDER BY start_time DESC
    """)
    
    scans = cursor.fetchall()
    
    if not scans:
        print("Aucun scan disponible")
        return
    
    print("\nScans disponibles:")
    print("-" * 80)
    print(f"{'Scan ID':<30} {'Date':<20} {'Fichiers':>12} {'Taille':>15}")
    print("-" * 80)
    
    for scan in scans:
        scan_id = scan[0]
        date = format_timestamp(scan[1])
        files = f"{scan[2]:,}"
        size = format_size(scan[3])
        print(f"{scan_id:<30} {date:<20} {files:>12} {size:>15}")


def main():
    parser = argparse.ArgumentParser(
        description="Export résultats d'un scan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Lister les scans disponibles
  python scripts/export_results.py --list
  
  # Export CSV
  python scripts/export_results.py --scan-id scan_20251004 --format csv --output export.csv
  
  # Export JSON
  python scripts/export_results.py --scan-id scan_20251004 --format json --output export.json
  
  # Export Excel
  python scripts/export_results.py --scan-id scan_20251004 --format excel --output export.xlsx
        """
    )
    
    parser.add_argument('--scan-id', help="Scan ID à exporter")
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help="Format d'export")
    parser.add_argument('--output', help="Chemin fichier de sortie")
    parser.add_argument('--config', default='config.yaml', help="Fichier de configuration")
    parser.add_argument('--list', action='store_true', help="Lister les scans disponibles")
    
    args = parser.parse_args()
    
    # Charger config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Fichier config introuvable: {args.config}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Setup logging
    setup_logging(config)
    
    # Connexion DB
    db_path = config['database']['path']
    if not Path(db_path).exists():
        print(f"❌ Base de données introuvable: {db_path}")
        sys.exit(1)
    
    db = DatabaseManager(db_path)
    db.connect()
    
    try:
        # Lister scans si demandé
        if args.list:
            list_scans(db)
            return
        
        # Vérifier arguments
        if not args.scan_id:
            print("❌ --scan-id requis (ou utilisez --list)")
            parser.print_help()
            sys.exit(1)
        
        if not args.output:
            print("❌ --output requis")
            parser.print_help()
            sys.exit(1)
        
        # Vérifier que scan existe
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scans WHERE scan_id = ?", (args.scan_id,))
        if cursor.fetchone()[0] == 0:
            print(f"❌ Scan introuvable: {args.scan_id}")
            print("\nUtilisez --list pour voir les scans disponibles")
            sys.exit(1)
        
        # Export
        print(f"\nExport du scan '{args.scan_id}' en {args.format.upper()}...")
        
        if args.format == 'csv':
            export_csv(db, args.scan_id, args.output)
        elif args.format == 'json':
            export_json(db, args.scan_id, args.output)
        elif args.format == 'excel':
            export_excel(db, args.scan_id, args.output)
        
    finally:
        db.close()


if __name__ == '__main__':
    main()
