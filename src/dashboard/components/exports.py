"""
Page Exports - Génération et téléchargement de rapports.
Phase 3.3 - Implémentation complète
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size, format_timestamp

# ============================================================================
# EXPORT CSV
# ============================================================================

@st.cache_data(ttl=60)
def export_to_csv(_db, scan_id: str, filters: dict = None):
    """
    Exporte données en CSV.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        filters: Filtres optionnels
        
    Returns:
        Bytes CSV encodé
    """
    from components.filters import apply_filters_to_query
    
    cursor = _db.conn.cursor()
    
    base_query = """
        SELECT 
            path,
            parent_dir,
            filename,
            extension,
            size_bytes,
            owner_name,
            group_name,
            permissions,
            mtime,
            atime
        FROM files
        WHERE scan_id = ?
    """
    
    params = [scan_id]
    
    if filters:
        query = apply_filters_to_query(base_query, filters, params)
    else:
        query = base_query
    
    cursor.execute(query, params)
    
    # Récupérer données
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    
    df = pd.DataFrame(data, columns=columns)
    
    # Formater colonnes
    df['size_formatted'] = df['size_bytes'].apply(format_size)
    df['mtime_formatted'] = df['mtime'].apply(format_timestamp)
    
    # Convertir en CSV
    csv = df.to_csv(index=False).encode('utf-8')
    
    return csv

# ============================================================================
# EXPORT EXCEL
# ============================================================================

@st.cache_data(ttl=60)
def export_to_excel(_db, scan_id: str, filters: dict = None):
    """
    Exporte données en Excel avec formatage.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        filters: Filtres optionnels
        
    Returns:
        Bytes Excel
    """
    from components.filters import apply_filters_to_query
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        st.error("⚠️ Module openpyxl non installé. Utilisez: pip install openpyxl")
        return None
    
    cursor = _db.conn.cursor()
    
    # Récupérer données fichiers
    base_query = """
        SELECT 
            path, filename, extension, size_bytes,
            owner_name, group_name, permissions,
            mtime
        FROM files
        WHERE scan_id = ?
    """
    
    params = [scan_id]
    
    if filters:
        query = apply_filters_to_query(base_query, filters, params)
    else:
        query = base_query
    
    cursor.execute(query, params)
    
    columns = ['Chemin', 'Nom', 'Extension', 'Taille (bytes)', 
               'Propriétaire', 'Groupe', 'Permissions', 'Date modification']
    data = cursor.fetchall()
    
    df_files = pd.DataFrame(data, columns=columns)
    
    # Formater
    df_files['Taille'] = df_files['Taille (bytes)'].apply(format_size)
    df_files['Date'] = df_files['Date modification'].apply(format_timestamp)
    
    # Récupérer statistiques
    cursor.execute("""
        SELECT id, start_time, end_time, total_files, total_size_bytes
        FROM scans
        WHERE id = ?
    """, (scan_id,))
    
    scan_info = cursor.fetchone()
    
    # Créer fichier Excel
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Feuille informations
        df_info = pd.DataFrame([{
            'Scan ID': scan_info[0],
            'Date début': format_timestamp(scan_info[1]),
            'Date fin': format_timestamp(scan_info[2]),
            'Total fichiers': f"{scan_info[3]:,}",
            'Taille totale': format_size(scan_info[4])
        }])
        df_info.to_excel(writer, sheet_name='Informations', index=False)
        
        # Feuille fichiers (limiter à 100k lignes pour Excel)
        df_export = df_files[['Nom', 'Taille', 'Propriétaire', 'Date', 'Chemin']].head(100000)
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
        
        # Formatage
        workbook = writer.book
        
        # Formater feuille Informations
        ws_info = workbook['Informations']
        for cell in ws_info[1]:  # Header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
    
    output.seek(0)
    return output.getvalue()

# ============================================================================
# EXPORT JSON
# ============================================================================

@st.cache_data(ttl=60)
def export_to_json(_db, scan_id: str, filters: dict = None):
    """
    Exporte données en JSON.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        filters: Filtres optionnels
        
    Returns:
        String JSON
    """
    from components.filters import apply_filters_to_query
    
    cursor = _db.conn.cursor()
    
    # Informations scan
    cursor.execute("""
        SELECT id, start_time, end_time, total_files, total_size_bytes
        FROM scans
        WHERE id = ?
    """, (scan_id,))
    
    scan_row = cursor.fetchone()
    
    scan_info = {
        'scan_id': scan_row[0],
        'start_time': scan_row[1],
        'end_time': scan_row[2],
        'total_files': scan_row[3],
        'total_size_bytes': scan_row[4]
    }
    
    # Fichiers (limiter à 50k pour JSON)
    base_query = """
        SELECT 
            path, filename, extension, size_bytes,
            owner_name, mtime
        FROM files
        WHERE scan_id = ?
    """
    
    params = [scan_id]
    
    if filters:
        query = apply_filters_to_query(base_query, filters, params)
    else:
        query = base_query
    
    query += " LIMIT 50000"
    
    cursor.execute(query, params)
    
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
    
    # Assembler JSON
    export_data = {
        'scan': scan_info,
        'files': files,
        'export_date': datetime.now().isoformat(),
        'files_count': len(files)
    }
    
    return json.dumps(export_data, indent=2)

# ============================================================================
# RENDER PAGE EXPORTS
# ============================================================================

def render_exports(db, scan_id: str):
    """
    Page principale d'export.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan sélectionné
    """
    st.title("💾 Exports")
    st.markdown("---")
    
    st.info("Exportez les données du scan dans différents formats")
    
    # Sélection format
    st.subheader("📁 Format d'export")
    
    export_format = st.radio(
        "Choisissez un format",
        options=['CSV', 'Excel', 'JSON'],
        horizontal=True
    )
    
    # Options d'export
    st.subheader("⚙️ Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_filters = st.checkbox(
            "Appliquer les filtres actifs",
            value=False,
            help="Si activé, seuls les fichiers filtrés seront exportés"
        )
    
    with col2:
        max_rows = st.number_input(
            "Nombre max de lignes",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=1000,
            help="Limite le nombre de fichiers exportés"
        )
    
    # Récupérer filtres actifs si nécessaire
    filters = None
    if include_filters and st.session_state.get('filters_active'):
        filters = st.session_state.get('current_filters', {})
        st.success(f"✅ {len(filters)} filtre(s) seront appliqués")
    
    # Bouton export
    st.markdown("---")
    st.subheader("📥 Téléchargement")
    
    if st.button("🚀 Générer export", type="primary", use_container_width=True):
        with st.spinner(f"Génération de l'export {export_format}..."):
            try:
                # Générer selon format
                if export_format == 'CSV':
                    data = export_to_csv(db, scan_id, filters)
                    filename = f"export_{scan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    mime = "text/csv"
                    
                elif export_format == 'Excel':
                    data = export_to_excel(db, scan_id, filters)
                    if data is None:
                        return
                    filename = f"export_{scan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    
                elif export_format == 'JSON':
                    data = export_to_json(db, scan_id, filters)
                    filename = f"export_{scan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    mime = "application/json"
                
                # Bouton download
                st.download_button(
                    label=f"⬇️ Télécharger {export_format}",
                    data=data,
                    file_name=filename,
                    mime=mime,
                    use_container_width=True
                )
                
                st.success(f"✅ Export {export_format} généré avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'export: {e}")
    
    # Informations utiles
    st.markdown("---")
    st.info("""
    **ℹ️ Informations:**
    - **CSV**: Format universel, facile à ouvrir avec Excel/LibreOffice
    - **Excel**: Format avec formatage et plusieurs feuilles (limité à 100k lignes)
    - **JSON**: Format structuré pour traitement programmatique (limité à 50k fichiers)
    """)
