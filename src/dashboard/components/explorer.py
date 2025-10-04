"""
Page Explorer - Navigation dans l'arborescence et exploration des fichiers.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from typing import Optional, List
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size, format_timestamp

# ============================================================================
# RÉCUPÉRATION DONNÉES ARBORESCENCE
# ============================================================================

@st.cache_data(ttl=300)
def get_root_directories(_db, scan_id: str):
    """
    Récupère les dossiers racine du scan.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        
    Returns:
        Liste de chemins racine
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT DISTINCT parent_dir
        FROM files
        WHERE scan_id = ?
        ORDER BY parent_dir
    """, (scan_id,))
    
    # Extraire dossiers de premier niveau
    all_dirs = [row[0] for row in cursor.fetchall()]
    
    # Trouver racines (chemins les plus courts)
    roots = []
    for dir_path in sorted(all_dirs, key=len):
        # Vérifier si c'est une racine (pas de parent dans la liste)
        is_root = True
        for other in roots:
            if dir_path.startswith(other + '/'):
                is_root = False
                break
        if is_root:
            roots.append(dir_path)
    
    return sorted(roots)

@st.cache_data(ttl=300)
def get_subdirectories(_db, scan_id: str, parent_path: str):
    """
    Récupère les sous-dossiers d'un dossier parent.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        parent_path: Chemin du dossier parent
        
    Returns:
        Liste de sous-dossiers
    """
    cursor = _db.conn.cursor()
    
    # Récupérer dossiers enfants directs
    cursor.execute("""
        SELECT DISTINCT parent_dir
        FROM files
        WHERE scan_id = ?
          AND parent_dir LIKE ?
          AND parent_dir != ?
        ORDER BY parent_dir
    """, (scan_id, f"{parent_path}/%", parent_path))
    
    all_subdirs = [row[0] for row in cursor.fetchall()]
    
    # Filtrer pour ne garder que les enfants directs
    parent_depth = parent_path.count('/')
    direct_children = []
    
    for subdir in all_subdirs:
        if subdir.count('/') == parent_depth + 1:
            direct_children.append(subdir)
    
    return sorted(direct_children)

@st.cache_data(ttl=300)
def get_directory_stats(_db, scan_id: str, dir_path: str):
    """
    Récupère statistiques d'un dossier.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        dir_path: Chemin du dossier
        
    Returns:
        Dict avec stats ou None
    """
    cursor = _db.conn.cursor()
    
    # Tenter d'obtenir depuis directory_stats
    cursor.execute("""
        SELECT total_files, total_size_bytes, extension_stats
        FROM directory_stats
        WHERE scan_id = ? AND dir_path = ?
    """, (scan_id, dir_path))
    
    row = cursor.fetchone()
    if row:
        return {
            'total_files': row[0],
            'total_size': row[1],
            'extensions': json.loads(row[2]) if row[2] else {}
        }
    
    # Sinon calculer à la volée
    cursor.execute("""
        SELECT 
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND parent_dir = ?
    """, (scan_id, dir_path))
    
    row = cursor.fetchone()
    return {
        'total_files': row[0] or 0,
        'total_size': row[1] or 0,
        'extensions': {}
    }

@st.cache_data(ttl=300)
def get_files_in_directory(_db, scan_id: str, dir_path: str, 
                          filters: dict = None,
                          limit: int = 1000, offset: int = 0):
    """
    Récupère fichiers d'un dossier.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        dir_path: Chemin du dossier
        filters: Filtres à appliquer (optionnel)
        limit: Limite de résultats
        offset: Offset pagination
        
    Returns:
        DataFrame avec fichiers
    """
    from .filters import apply_filters_to_query
    
    cursor = _db.conn.cursor()
    
    base_query = """
        SELECT 
            filename,
            size_bytes,
            owner_name,
            group_name,
            mtime,
            permissions,
            extension
        FROM files
        WHERE scan_id = ? AND parent_dir = ?
    """
    
    params = [scan_id, dir_path]
    
    # Appliquer filtres
    if filters:
        query = apply_filters_to_query(base_query, filters, params)
    else:
        query = base_query
    
    query += " ORDER BY size_bytes DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    data = cursor.fetchall()
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=[
        'Nom', 'Taille (bytes)', 'Propriétaire', 'Groupe',
        'Date modification', 'Permissions', 'Extension'
    ])
    
    # Formatage
    df['Taille'] = df['Taille (bytes)'].apply(format_size)
    df['Date'] = df['Date modification'].apply(format_timestamp)
    
    # Réorganiser colonnes
    df = df[['Nom', 'Taille', 'Propriétaire', 'Groupe', 'Date', 'Permissions', 'Extension']]
    
    return df

@st.cache_data(ttl=300)
def count_files_in_directory(_db, scan_id: str, dir_path: str):
    """
    Compte nombre total de fichiers dans dossier.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        dir_path: Chemin du dossier
        
    Returns:
        Nombre de fichiers
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM files
        WHERE scan_id = ? AND parent_dir = ?
    """, (scan_id, dir_path))
    
    return cursor.fetchone()[0]

# ============================================================================
# COMPOSANTS UI NAVIGATION
# ============================================================================

def navigate_directory(db, scan_id: str):
    """
    Interface de navigation dans l'arborescence.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        
    Returns:
        Chemin du dossier sélectionné
    """
    # État de navigation (stocké dans session)
    if 'current_path' not in st.session_state:
        # Initialiser avec premier dossier racine
        roots = get_root_directories(db, scan_id)
        st.session_state.current_path = roots[0] if roots else '/'
    
    current_path = st.session_state.current_path
    
    # Afficher racines disponibles
    roots = get_root_directories(db, scan_id)
    
    st.subheader("📁 Navigation")
    
    # Déterminer la racine du chemin actuel
    current_root = current_path
    for root in roots:
        if current_path.startswith(root):
            current_root = root
            break
    
    # Sélecteur racine
    selected_root = st.selectbox(
        "Dossier racine",
        options=roots,
        index=roots.index(current_root) if current_root in roots else 0,
        key='root_selector'
    )
    
    # Si changement de racine, réinitialiser au niveau de la racine
    if selected_root != current_root:
        st.session_state.current_path = selected_root
        current_path = selected_root
        st.rerun()
    
    # Afficher breadcrumb
    st.caption("Chemin actuel:")
    st.code(current_path, language=None)
    
    # Récupérer sous-dossiers
    subdirs = get_subdirectories(db, scan_id, current_path)
    
    if subdirs:
        st.caption(f"Sous-dossiers ({len(subdirs)}) :")
        
        # Afficher sous-dossiers avec boutons
        for subdir in subdirs[:20]:  # Limiter à 20 pour performance
            subdir_name = subdir.split('/')[-1]
            if st.button(f"📂 {subdir_name}", key=f"nav_{subdir}", use_container_width=True):
                st.session_state.current_path = subdir
                st.rerun()
        
        if len(subdirs) > 20:
            st.caption(f"... et {len(subdirs) - 20} autres dossiers")
    else:
        st.info("Aucun sous-dossier")
    
    # Bouton retour parent
    if current_path != '/' and '/' in current_path:
        st.markdown("---")
        parent_path = '/'.join(current_path.split('/')[:-1])
        if not parent_path:
            parent_path = '/'
        if st.button("⬆️ Dossier parent", use_container_width=True):
            st.session_state.current_path = parent_path
            st.rerun()
    
    return current_path

def display_directory_info(db, scan_id: str, dir_path: str):
    """
    Affiche informations sur le dossier sélectionné.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        dir_path: Chemin du dossier
    """
    stats = get_directory_stats(db, scan_id, dir_path)
    
    st.subheader("📊 Informations Dossier")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Nombre de fichiers",
            f"{stats['total_files']:,}"
        )
    
    with col2:
        st.metric(
            "Taille totale",
            format_size(stats['total_size'])
        )
    
    # Répartition extensions si disponible
    if stats['extensions']:
        st.caption("Répartition par extension:")
        ext_data = []
        for ext, count in sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)[:10]:
            ext_data.append({
                'Extension': ext or 'sans extension',
                'Fichiers': count
            })
        ext_df = pd.DataFrame(ext_data)
        st.dataframe(ext_df, hide_index=True, use_container_width=True)

def display_files_table(db, scan_id: str, dir_path: str, filters: dict = None):
    """
    Affiche tableau des fichiers avec pagination.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        dir_path: Chemin du dossier
        filters: Filtres à appliquer
    """
    # Compter fichiers
    total_files = count_files_in_directory(db, scan_id, dir_path)
    
    if total_files == 0:
        st.info("📭 Aucun fichier dans ce dossier")
        return
    
    st.markdown("---")
    st.subheader("📄 Fichiers")
    st.caption(f"**{total_files:,} fichiers** dans ce dossier")
    
    # Configuration pagination
    page_size = st.selectbox(
        "Fichiers par page",
        options=[50, 100, 500, 1000],
        index=1,
        key='page_size'
    )
    
    # Calculer nombre de pages
    total_pages = (total_files + page_size - 1) // page_size
    
    # Sélecteur page
    if total_pages > 1:
        page = st.number_input(
            f"Page (1 à {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key='page_number'
        )
    else:
        page = 1
    
    # Calculer offset
    offset = (page - 1) * page_size
    
    # Récupérer données
    df = get_files_in_directory(db, scan_id, dir_path, filters=filters, limit=page_size, offset=offset)
    
    if df.empty:
        st.warning("Aucune donnée à afficher")
        return
    
    # Afficher tableau
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Bouton export CSV
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Export page courante
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export page (CSV)",
            data=csv_data,
            file_name=f"fichiers_page{page}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export complet (si < 10k fichiers)
        if total_files < 10000:
            df_full = get_files_in_directory(db, scan_id, dir_path, filters=filters, limit=total_files, offset=0)
            csv_full = df_full.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export complet (CSV)",
                data=csv_full,
                file_name=f"fichiers_complet.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Export complet disponible si < 10k fichiers")

# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_explorer(db, scan_id: str):
    """
    Fonction principale de rendu de la page Explorer.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
    """
    st.title("🔍 Explorateur de Fichiers")
    st.markdown("---")
    
    # Afficher filtres dans sidebar
    from .filters import render_filters_sidebar
    filters = render_filters_sidebar(db, scan_id)
    
    # Layout 2 colonnes
    col_nav, col_content = st.columns([1, 2])
    
    with col_nav:
        # Navigation arborescence
        current_path = navigate_directory(db, scan_id)
    
    with col_content:
        # Informations dossier
        display_directory_info(db, scan_id, current_path)
        
        # Tableau fichiers
        display_files_table(db, scan_id, current_path, filters=filters)
