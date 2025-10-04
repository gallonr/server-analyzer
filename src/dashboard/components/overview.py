"""
Page Vue d'ensemble - Statistiques globales et graphiques principaux.
Phase 3.3 - Optimisations performance et UX
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Import utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size, format_timestamp

# Import optimisations Phase 3.3
try:
    from dashboard.performance import profile_query, get_optimal_ttl
    from dashboard.ui_constants import ICONS, TOOLTIPS, get_help
except ImportError:
    # Fallback si modules non disponibles
    def profile_query(f): return f
    def get_optimal_ttl(t): return 300
    ICONS = {}
    TOOLTIPS = {}
    def get_help(t, d=""): return d

# ============================================================================
# RÉCUPÉRATION DONNÉES - AVEC PROFILING
# ============================================================================

@st.cache_data(ttl=600)  # Augmenté à 10 min (Phase 3.3)
@profile_query
def get_scan_info(_db, scan_id: str):
    """
    Récupère informations globales du scan.
    
    Returns:
        dict avec infos scan
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT id, start_time, end_time, total_files, 
               total_size_bytes, status
        FROM scans
        WHERE id = ?
    """, (scan_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    # Calculer le nombre de dossiers depuis la table files
    cursor.execute("""
        SELECT COUNT(*) FROM files
        WHERE scan_id = ? AND is_directory = 1
    """, (scan_id,))
    total_dirs = cursor.fetchone()[0]
    
    return {
        'scan_id': row[0],
        'start_time': row[1],
        'end_time': row[2],
        'total_files': row[3],
        'total_size': row[4],
        'total_dirs': total_dirs,
        'status': row[5],
        'duration': (row[2] - row[1]) if row[2] and row[1] else 0
    }

@st.cache_data(ttl=600)  # Augmenté à 10 min (Phase 3.3)
@profile_query
def get_top_extensions(_db, scan_id: str, limit: int = 10):
    """
    Récupère top N extensions par volume.
    
    Returns:
        DataFrame avec colonnes: extension, file_count, total_size
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(extension, 'sans_extension') as extension,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY extension
        ORDER BY total_size DESC
        LIMIT ?
    """, (scan_id, limit))
    
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=['extension', 'file_count', 'total_size'])

@st.cache_data(ttl=600)  # Augmenté à 10 min (Phase 3.3)
@profile_query
def get_top_owners(_db, scan_id: str, limit: int = 10):
    """
    Récupère top N propriétaires par volume.
    
    Returns:
        DataFrame
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(owner_name, 'unknown') as owner,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY owner_name
        ORDER BY total_size DESC
        LIMIT ?
    """, (scan_id, limit))
    
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=['owner', 'file_count', 'total_size'])

@st.cache_data(ttl=300)
def get_size_distribution(_db, scan_id: str):
    """
    Récupère distribution des tailles de fichiers.
    
    Returns:
        DataFrame avec colonnes: size_category, count
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT 
            CASE 
                WHEN size_bytes < 1024 THEN '< 1 KB'
                WHEN size_bytes < 1048576 THEN '1 KB - 1 MB'
                WHEN size_bytes < 10485760 THEN '1 MB - 10 MB'
                WHEN size_bytes < 104857600 THEN '10 MB - 100 MB'
                WHEN size_bytes < 1073741824 THEN '100 MB - 1 GB'
                ELSE '> 1 GB'
            END as size_category,
            COUNT(*) as count
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY size_category
        ORDER BY 
            CASE 
                WHEN size_bytes < 1024 THEN 1
                WHEN size_bytes < 1048576 THEN 2
                WHEN size_bytes < 10485760 THEN 3
                WHEN size_bytes < 104857600 THEN 4
                WHEN size_bytes < 1073741824 THEN 5
                ELSE 6
            END
    """, (scan_id,))
    
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=['size_category', 'count'])

# ============================================================================
# COMPOSANTS UI
# ============================================================================

def display_metrics(scan_info: dict):
    """
    Affiche métriques principales sous forme de cards.
    Phase 3.3 - Avec tooltips améliorés
    
    Args:
        scan_info: Dictionnaire avec infos scan
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"{ICONS.get('file', '📁')} Total Fichiers",
            value=f"{scan_info['total_files']:,}",
            help=TOOLTIPS.get('total_files', "Nombre total de fichiers scannés")
        )
    
    with col2:
        st.metric(
            label=f"{ICONS.get('size', '💾')} Taille Totale",
            value=format_size(scan_info['total_size']),
            help=TOOLTIPS.get('total_size', "Volume total des données")
        )
    
    with col3:
        st.metric(
            label=f"{ICONS.get('folder', '📂')} Dossiers",
            value=f"{scan_info['total_dirs']:,}",
            help=TOOLTIPS.get('total_dirs', "Nombre total de dossiers")
        )
    
    with col4:
        duration_minutes = scan_info['duration'] / 60 if scan_info['duration'] else 0
        st.metric(
            label=f"{ICONS.get('time', '⏱️')} Durée Scan",
            value=f"{duration_minutes:.1f} min",
            help=TOOLTIPS.get('scan_duration', "Durée du scan")
        )

def display_top_extensions_chart(df: pd.DataFrame):
    """
    Affiche graphique des top extensions.
    
    Args:
        df: DataFrame avec colonnes extension, file_count, total_size
    """
    if df.empty:
        st.warning("Aucune donnée disponible")
        return
    
    # Ajouter colonne formatée
    df['total_size_formatted'] = df['total_size'].apply(format_size)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['extension'],
        y=df['total_size'],
        name='Volume',
        marker_color='steelblue',
        text=df['total_size_formatted'],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Volume: %{text}<br>Fichiers: %{customdata:,}<extra></extra>',
        customdata=df['file_count']
    ))
    
    fig.update_layout(
        title="Top 10 Extensions par Volume",
        xaxis_title="Extension",
        yaxis_title="Taille (bytes)",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_top_owners_chart(df: pd.DataFrame):
    """
    Affiche graphique des top propriétaires.
    
    Args:
        df: DataFrame avec colonnes owner, file_count, total_size
    """
    if df.empty:
        st.warning("Aucune donnée disponible")
        return
    
    # Ajouter colonne formatée
    df['total_size_formatted'] = df['total_size'].apply(format_size)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['owner'],
        y=df['total_size'],
        name='Volume',
        marker_color='coral',
        text=df['total_size_formatted'],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Volume: %{text}<br>Fichiers: %{customdata:,}<extra></extra>',
        customdata=df['file_count']
    ))
    
    fig.update_layout(
        title="Top 10 Propriétaires par Volume",
        xaxis_title="Propriétaire",
        yaxis_title="Taille (bytes)",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_size_distribution_chart(df: pd.DataFrame):
    """
    Affiche distribution des tailles de fichiers.
    
    Args:
        df: DataFrame avec colonnes size_category, count
    """
    if df.empty:
        st.warning("Aucune donnée disponible")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['size_category'],
        y=df['count'],
        marker_color='mediumseagreen',
        text=df['count'],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Fichiers: %{y:,}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribution des Tailles de Fichiers",
        xaxis_title="Catégorie de Taille",
        yaxis_title="Nombre de Fichiers",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_overview(db, scan_id: str):
    """
    Affiche la page vue d'ensemble.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan à afficher
    """
    st.title("🏠 Vue d'ensemble")
    st.markdown("---")
    
    # Récupérer infos scan
    scan_info = get_scan_info(db, scan_id)
    
    if not scan_info:
        st.error(f"❌ Scan introuvable: {scan_id}")
        return
    
    # Afficher métriques principales
    st.subheader("📊 Statistiques Globales")
    display_metrics(scan_info)
    
    st.markdown("---")
    
    # Afficher informations temporelles
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🕐 **Début du scan**: {format_timestamp(scan_info['start_time'])}")
    with col2:
        st.info(f"✅ **Statut**: {scan_info['status']}")
    
    st.markdown("---")
    
    # Section graphiques
    st.subheader("📈 Visualisations")
    
    # Top extensions
    with st.spinner("Chargement des données extensions..."):
        df_extensions = get_top_extensions(db, scan_id, limit=10)
        display_top_extensions_chart(df_extensions)
    
    st.markdown("---")
    
    # Top propriétaires
    with st.spinner("Chargement des données propriétaires..."):
        df_owners = get_top_owners(db, scan_id, limit=10)
        display_top_owners_chart(df_owners)
    
    st.markdown("---")
    
    # Distribution tailles
    with st.spinner("Chargement distribution tailles..."):
        df_sizes = get_size_distribution(db, scan_id)
        display_size_distribution_chart(df_sizes)
    
    st.markdown("---")
    
    # Section visualisations avancées
    st.subheader("📊 Visualisations Avancées")
    
    # Tabs pour organiser les graphiques
    tab1, tab2, tab3 = st.tabs(["🥧 Répartition", "🌳 Hiérarchie", "📅 Temporel"])
    
    with tab1:
        st.markdown("### Répartition des Extensions")
        with st.spinner("Génération du pie chart..."):
            from .charts import create_extensions_pie_chart
            df_ext = get_top_extensions(db, scan_id, limit=15)
            fig_pie = create_extensions_pie_chart(df_ext)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab2:
        st.markdown("### Volumes Hiérarchiques par Dossier")
        with st.spinner("Génération du treemap..."):
            from .charts import get_directory_hierarchy, create_treemap
            df_tree = get_directory_hierarchy(db, scan_id, max_depth=3)
            fig_tree = create_treemap(df_tree)
            st.plotly_chart(fig_tree, use_container_width=True)
    
    with tab3:
        st.markdown("### Distribution Temporelle des Fichiers")
        
        # Sélecteur de période
        col1, col2 = st.columns([3, 1])
        with col2:
            period = st.selectbox(
                "Grouper par",
                options=['month', 'year', 'day'],
                format_func=lambda x: {'day': 'Jour', 'month': 'Mois', 'year': 'Année'}[x],
                help="Choisir la granularité temporelle"
            )
        
        with st.spinner("Génération de la timeline..."):
            from .charts import get_temporal_data, create_timeline_chart
            df_time = get_temporal_data(db, scan_id, groupby=period)
            fig_time = create_timeline_chart(df_time)
            st.plotly_chart(fig_time, use_container_width=True)
    
    # Bouton refresh
    st.markdown("---")
    if st.button("🔄 Rafraîchir les données", type="primary"):
        st.cache_data.clear()
        st.rerun()
