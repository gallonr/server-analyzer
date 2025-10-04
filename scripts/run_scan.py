#!/usr/bin/env python3
"""
Script principal pour lancer un scan du serveur.

Usage:
    python scripts/run_scan.py [--config CONFIG_PATH]
"""

import sys
import argparse
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import setup_logging, load_config, format_size
from src.database import DatabaseManager
from src.scanner import ParallelScanner
from src.stats import (
    compute_directory_stats,
    compute_extension_stats,
    get_top_extensions,
    compute_owner_stats,
    get_top_owners,
    detect_large_files,
    detect_old_files,
    detect_duplicate_candidates
)

import logging

logger = logging.getLogger('server_analyzer')


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description='Lance un scan complet du serveur'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Chemin vers le fichier de configuration (défaut: config.yaml)'
    )
    parser.add_argument(
        '--skip-stats',
        action='store_true',
        help='Ne pas calculer les statistiques après le scan'
    )
    return parser.parse_args()


def main():
    """Fonction principale du script."""
    # Parse arguments
    args = parse_arguments()
    
    try:
        # Charger configuration
        print(f"Chargement de la configuration: {args.config}")
        config = load_config(args.config)
        
        # Configurer logging
        logger = setup_logging(config)
        logger.info("=" * 80)
        logger.info("Démarrage du scan serveur")
        logger.info("=" * 80)
        
        # Initialiser base de données
        db_path = config['database']['path']
        logger.info(f"Connexion à la base de données: {db_path}")
        db = DatabaseManager(db_path)
        db.connect()
        db.init_schema()
        
        # Créer un nouveau scan
        root_paths = config['root_paths']
        num_workers = config['performance']['num_workers']
        
        logger.info(f"Chemins racine à scanner: {root_paths}")
        logger.info(f"Nombre de workers: {num_workers}")
        
        scan_id = db.create_scan(
            root_paths=root_paths,
            num_workers=num_workers,
            config_snapshot=json.dumps(config, indent=2)
        )
        
        logger.info(f"Scan ID: {scan_id}")
        
        # Initialiser le scanner
        exclusions = config.get('exclusions', {'directories': [], 'extensions': []})
        batch_size = config['performance'].get('batch_size', 50000)
        checkpoint_interval = config['performance'].get('checkpoint_interval', 300)
        
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=num_workers,
            exclusions=exclusions,
            batch_size=batch_size
        )
        
        # Lancer le scan
        logger.info("Lancement du scan parallélisé...")
        stats = scanner.scan(
            root_paths=root_paths,
            db_manager=db,
            checkpoint_interval=checkpoint_interval
        )
        
        # Mettre à jour le statut final
        total_files = db.get_total_files_count(scan_id)
        total_size = db.get_total_size(scan_id)
        
        db.update_scan_status(
            scan_id=scan_id,
            status='completed',
            total_files=total_files,
            total_size=total_size,
            errors_count=stats.get('errors', 0)
        )
        
        # Afficher résumé
        logger.info("=" * 80)
        logger.info("SCAN TERMINÉ AVEC SUCCÈS")
        logger.info("=" * 80)
        logger.info(f"Scan ID: {scan_id}")
        logger.info(f"Fichiers scannés: {total_files:,}")
        logger.info(f"Taille totale: {format_size(total_size)}")
        logger.info(f"Répertoires traités: {stats.get('directories_scanned', 0):,}")
        logger.info(f"Durée: {stats.get('duration_seconds', 0):.2f} secondes")
        logger.info(f"Débit: {stats.get('files_per_second', 0):.2f} fichiers/seconde")
        
        if stats.get('errors', 0) > 0:
            logger.warning(f"Erreurs rencontrées: {stats['errors']}")
        
        logger.info("=" * 80)
        
        # Calculer les statistiques si demandé
        if not args.skip_stats:
            logger.info("=" * 80)
            logger.info("CALCUL DES STATISTIQUES")
            logger.info("=" * 80)
            
            # Stats par dossier
            logger.info("Calcul des statistiques par dossier...")
            dir_count = compute_directory_stats(scan_id, db.conn)
            logger.info(f"✓ Statistiques calculées pour {dir_count:,} dossiers")
            
            # Stats par extension
            logger.info("Calcul des statistiques par extension...")
            ext_stats = compute_extension_stats(scan_id, db.conn)
            logger.info(f"✓ Statistiques calculées pour {len(ext_stats)} extensions")
            
            # Top extensions
            top_ext = get_top_extensions(scan_id, db.conn, limit=10, by='size')
            if top_ext:
                logger.info("Top 10 extensions par taille:")
                for ext, count, size in top_ext[:5]:
                    logger.info(f"  - .{ext if ext else 'sans_ext'}: {count:,} fichiers, {format_size(size)}")
            
            # Stats par propriétaire
            logger.info("Calcul des statistiques par propriétaire...")
            owner_stats = compute_owner_stats(scan_id, db.conn)
            logger.info(f"✓ Statistiques calculées pour {len(owner_stats)} propriétaires")
            
            # Top propriétaires
            top_owners = get_top_owners(scan_id, db.conn, limit=10)
            if top_owners:
                logger.info("Top 5 propriétaires par volume:")
                for owner, count, size in top_owners[:5]:
                    logger.info(f"  - {owner}: {count:,} fichiers, {format_size(size)}")
            
            # Détection d'anomalies
            logger.info("Détection d'anomalies...")
            config_alerts = config.get('alerts', {})
            
            # Fichiers volumineux (défaut: 10 GB)
            large_threshold = config_alerts.get('large_file_threshold', 10*1024*1024*1024)
            large_files = detect_large_files(scan_id, db.conn, large_threshold)
            if large_files:
                logger.warning(f"⚠️  {len(large_files)} fichiers > {format_size(large_threshold)}")
                for f in large_files[:5]:
                    logger.warning(f"  - {f['path']}: {format_size(f['size_bytes'])}")
            
            # Fichiers anciens (défaut: 2 ans = 730 jours)
            old_threshold = config_alerts.get('old_file_threshold', 730)
            old_files = detect_old_files(scan_id, db.conn, old_threshold)
            if old_files:
                logger.warning(f"⚠️  {len(old_files)} fichiers non modifiés depuis > {old_threshold} jours")
                for f in old_files[:5]:
                    import datetime
                    date = datetime.datetime.fromtimestamp(f['mtime']).strftime('%Y-%m-%d')
                    logger.warning(f"  - {f['path']}: {date}")
            
            # Doublons potentiels
            duplicates = detect_duplicate_candidates(scan_id, db.conn)
            if duplicates:
                logger.warning(f"⚠️  {len(duplicates)} groupes de doublons potentiels détectés")
                for dup in duplicates[:5]:
                    logger.warning(f"  - {dup['name']} ({format_size(dup['size_bytes'])}): {dup['count']} copies")
            
            logger.info("=" * 80)
            logger.info("✓ Statistiques calculées avec succès")
            logger.info("=" * 80)
        
        # Fermer la connexion
        db.close()
        
        print("\n✅ Scan terminé avec succès!")
        print(f"📊 Résultats: {total_files:,} fichiers, {format_size(total_size)}")
        print(f"💾 Base de données: {db_path}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Scan interrompu par l'utilisateur")
        if 'db' in locals() and 'scan_id' in locals():
            db.update_scan_status(scan_id, 'interrupted')
            db.close()
        print("\n⚠️  Scan interrompu")
        return 1
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        if 'db' in locals() and 'scan_id' in locals():
            db.update_scan_status(scan_id, 'failed')
            db.close()
        print(f"\n❌ Erreur: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
