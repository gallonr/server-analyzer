"""
Application principale du dashboard Streamlit.
Point d'entrée pour l'analyse et la visualisation des données serveur.
"""

import streamlit as st
import sqlite3
import sys
from pathlib import Path
import logging

# Ajouter src/ au PYTHONPATH
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from database import DatabaseManager
from utils import format_size, format_timestamp

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')

# ============================================================================
# CONFIGURATION PAGE
# ============================================================================

st.set_page_config(
    page_title="Server Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/server-analyzer',
        'Report a bug': 'https://github.com/your-repo/server-analyzer/issues',
        'About': "# Server Analysis Dashboard\nVersion 1.0.0"
    }
)

# ============================================================================
# CONNEXION BASE DE DONNÉES
# ============================================================================

@st.cache_resource
def get_database_connection(db_path: str):
    """
    Obtient connexion base de données (mise en cache).
    
    Args:
        db_path: Chemin vers la base SQLite
        
    Returns:
        DatabaseManager connecté
    """
    db = DatabaseManager(db_path)
    db.connect()
    
    # Vérifier et créer table duplicate_groups si nécessaire
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='duplicate_groups'
    """)
    if not cursor.fetchone():
        logger.warning("Table duplicate_groups manquante, création automatique...")
        db.init_schema()
        logger.info("✅ Table duplicate_groups créée")
    
    logger.info(f"Connexion base: {db_path}")
    return db

# ============================================================================
# SÉLECTION SCAN
# ============================================================================

@st.cache_data(ttl=60)
def get_available_scans(_db: DatabaseManager):
    """
    Récupère liste des scans disponibles.
    
    Args:
        _db: DatabaseManager (préfixe _ pour éviter hashing)
        
    Returns:
        Liste de tuples (scan_id, timestamp, nb_files)
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT id, start_time, total_files
        FROM scans
        ORDER BY start_time DESC
    """)
    # Convert Row objects to list of tuples for pickle serialization
    return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

def select_scan_sidebar(db: DatabaseManager):
    """
    Affiche sélecteur de scan dans sidebar.
    
    Args:
        db: DatabaseManager
        
    Returns:
        scan_id sélectionné ou None
    """
    st.sidebar.title("📊 Server Analysis Dashboard")
    st.sidebar.markdown("---")
    
    scans = get_available_scans(db)
    
    if not scans:
        st.sidebar.error("❌ Aucun scan disponible")
        st.sidebar.info("💡 Lancez d'abord un scan avec `python scripts/run_scan.py`")
        return None
    
    # Formatter options
    scan_options = {}
    for scan_id, timestamp, nb_files in scans:
        label = f"{scan_id} - {format_timestamp(timestamp)} ({nb_files:,} fichiers)"
        scan_options[label] = scan_id
    
    selected_label = st.sidebar.selectbox(
        "🔍 Sélectionner un scan",
        options=list(scan_options.keys()),
        help="Choisissez le scan à analyser"
    )
    
    selected_scan_id = scan_options[selected_label]
    
    # Afficher infos scan sélectionné
    st.sidebar.success(f"✅ Scan: **{selected_scan_id}**")
    
    return selected_scan_id

# ============================================================================
# NAVIGATION
# ============================================================================

def sidebar_navigation():
    """Affiche menu de navigation."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📑 Navigation")
    
    pages = {
        "🏠 Vue d'ensemble": "overview",
        "🔍 Explorateur": "explorer",
        "🔗 Doublons": "duplicates",
        "🔄 Comparaisons": "comparisons",
        "💾 Exports": "exports"
    }
    
    selected = st.sidebar.radio(
        "Sélectionnez une page",
        options=list(pages.keys()),
        label_visibility="collapsed"
    )
    
    return pages[selected]

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Point d'entrée principal de l'application."""
    
    # Configuration base de données depuis config ou argument
    import yaml
    from pathlib import Path
    
    # Charger config
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        db_path = config.get('database', {}).get('path', 'data/server_analysis.db')
    else:
        db_path = 'data/server_analysis.db'
    
    # Vérifier existence base
    if not Path(db_path).exists():
        st.error(f"❌ Base de données introuvable: `{db_path}`")
        st.info("💡 Lancez d'abord un scan avec `python scripts/run_scan.py`")
        st.stop()
    
    # Connexion
    try:
        db = get_database_connection(db_path)
    except Exception as e:
        st.error(f"❌ Erreur connexion base: {e}")
        st.stop()
    
    # Sélection scan
    scan_id = select_scan_sidebar(db)
    if not scan_id:
        st.warning("⚠️ Veuillez d'abord effectuer un scan")
        st.stop()
    
    # Navigation
    page = sidebar_navigation()
    
    # Afficher page sélectionnée
    if page == "overview":
        from components.overview import render_overview
        render_overview(db, scan_id)
    elif page == "explorer":
        from components.explorer import render_explorer
        render_explorer(db, scan_id)
    elif page == "duplicates":
        from components.duplicates import render_duplicates
        render_duplicates(db)
    elif page == "comparisons":
        from components.comparisons import render_comparisons
        render_comparisons(db)
    elif page == "exports":
        from components.exports import render_exports
        render_exports(db, scan_id)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Server Analysis Dashboard v1.0.0")
    st.sidebar.caption("© 2025")

if __name__ == "__main__":
    main()
