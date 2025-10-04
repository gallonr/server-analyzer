"""
Page Comparaisons - Comparaison entre deux scans.
Phase 3.3 - Implémentation complète
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size, format_timestamp

# ============================================================================
# RÉCUPÉRATION DONNÉES
# ============================================================================

@st.cache_data(ttl=300)
def get_available_scans_for_comparison(_db):
    """
    Récupère liste des scans disponibles.
    
    Returns:
        DataFrame avec scans
    """
    cursor = _db.conn.cursor()
    cursor.execute("""
        SELECT id, start_time, total_files, total_size_bytes
        FROM scans
        ORDER BY start_time DESC
    """)
    
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['scan_id', 'timestamp', 'files', 'size'])
    
    # Formater
    df['date'] = df['timestamp'].apply(format_timestamp)
    df['size_formatted'] = df['size'].apply(format_size)
    
    return df

# ============================================================================
# CALCUL DIFFÉRENTIEL
# ============================================================================

@st.cache_data(ttl=300)
def compute_comparison(_db, scan_id_1: str, scan_id_2: str):
    """
    Calcule différences entre deux scans.
    
    Args:
        _db: DatabaseManager
        scan_id_1: ID scan base
        scan_id_2: ID scan comparaison
        
    Returns:
        Dict avec résultats comparaison
    """
    cursor = _db.conn.cursor()
    
    # === NOUVEAUX FICHIERS ===
    # Fichiers dans scan_2 mais pas dans scan_1
    cursor.execute("""
        SELECT path, filename, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ?
          AND is_directory = 0
          AND path NOT IN (
              SELECT path FROM files WHERE scan_id = ? AND is_directory = 0
          )
        ORDER BY size_bytes DESC
        LIMIT 1000
    """, (scan_id_2, scan_id_1))
    
    new_files = cursor.fetchall()
    new_files_df = pd.DataFrame(new_files, columns=[
        'path', 'name', 'size_bytes', 'owner', 'mtime'
    ])
    
    # === FICHIERS SUPPRIMÉS ===
    cursor.execute("""
        SELECT path, filename, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ?
          AND is_directory = 0
          AND path NOT IN (
              SELECT path FROM files WHERE scan_id = ? AND is_directory = 0
          )
        ORDER BY size_bytes DESC
        LIMIT 1000
    """, (scan_id_1, scan_id_2))
    
    deleted_files = cursor.fetchall()
    deleted_files_df = pd.DataFrame(deleted_files, columns=[
        'path', 'name', 'size_bytes', 'owner', 'mtime'
    ])
    
    # === FICHIERS MODIFIÉS ===
    # Fichiers présents dans les 2 mais avec taille différente
    cursor.execute("""
        SELECT 
            f1.path,
            f1.filename,
            f1.size_bytes as size_1,
            f2.size_bytes as size_2,
            f1.mtime as mtime_1,
            f2.mtime as mtime_2
        FROM files f1
        INNER JOIN files f2 ON f1.path = f2.path
        WHERE f1.scan_id = ?
          AND f2.scan_id = ?
          AND f1.is_directory = 0
          AND f2.is_directory = 0
          AND (f1.size_bytes != f2.size_bytes OR f1.mtime != f2.mtime)
        ORDER BY ABS(f2.size_bytes - f1.size_bytes) DESC
        LIMIT 1000
    """, (scan_id_1, scan_id_2))
    
    modified_files = cursor.fetchall()
    modified_files_df = pd.DataFrame(modified_files, columns=[
        'path', 'name', 'size_1', 'size_2', 'mtime_1', 'mtime_2'
    ])
    
    if not modified_files_df.empty:
        modified_files_df['size_diff'] = modified_files_df['size_2'] - modified_files_df['size_1']
    
    # === STATISTIQUES GLOBALES ===
    cursor.execute("""
        SELECT total_files, total_size_bytes
        FROM scans
        WHERE scan_id = ?
    """, (scan_id_1,))
    stats_1 = cursor.fetchone()
    
    cursor.execute("""
        SELECT total_files, total_size_bytes
        FROM scans
        WHERE scan_id = ?
    """, (scan_id_2,))
    stats_2 = cursor.fetchone()
    
    return {
        'new_files': new_files_df,
        'deleted_files': deleted_files_df,
        'modified_files': modified_files_df,
        'stats': {
            'scan_1': {'files': stats_1[0], 'size': stats_1[1]},
            'scan_2': {'files': stats_2[0], 'size': stats_2[1]},
            'new_count': len(new_files_df),
            'deleted_count': len(deleted_files_df),
            'modified_count': len(modified_files_df)
        }
    }

# ============================================================================
# VISUALISATIONS
# ============================================================================

def create_evolution_chart(stats: dict):
    """
    Graphique évolution fichiers et volume.
    
    Args:
        stats: Statistiques comparaison
        
    Returns:
        Figure Plotly
    """
    # Données
    categories = ['Scan 1', 'Scan 2']
    files = [stats['scan_1']['files'], stats['scan_2']['files']]
    sizes = [stats['scan_1']['size'], stats['scan_2']['size']]
    
    # Figure avec double axe
    fig = go.Figure()
    
    # Barres nombre fichiers
    fig.add_trace(go.Bar(
        name='Nombre de fichiers',
        x=categories,
        y=files,
        yaxis='y1',
        marker_color='lightblue'
    ))
    
    # Ligne volume
    fig.add_trace(go.Scatter(
        name='Volume total',
        x=categories,
        y=sizes,
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='green', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title='Évolution Fichiers et Volume',
        xaxis=dict(title='Scan'),
        yaxis=dict(
            title='Nombre de fichiers',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='Volume (bytes)',
            titlefont=dict(color='green'),
            tickfont=dict(color='green'),
            overlaying='y',
            side='right'
        ),
        height=400,
        showlegend=True
    )
    
    return fig

def create_changes_pie_chart(stats: dict):
    """
    Pie chart répartition changements.
    
    Args:
        stats: Statistiques comparaison
        
    Returns:
        Figure Plotly
    """
    labels = ['Nouveaux', 'Supprimés', 'Modifiés']
    values = [stats['new_count'], stats['deleted_count'], stats['modified_count']]
    colors = ['green', 'red', 'orange']
    
    fig = px.pie(
        values=values,
        names=labels,
        title='Répartition des Changements',
        color=labels,
        color_discrete_map={'Nouveaux': 'green', 'Supprimés': 'red', 'Modifiés': 'orange'}
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

# ============================================================================
# AFFICHAGE RÉSULTATS
# ============================================================================

def display_comparison_results(comparison: dict):
    """
    Affiche résultats de comparaison.
    
    Args:
        comparison: Dict retourné par compute_comparison()
    """
    stats = comparison['stats']
    
    # === MÉTRIQUES GLOBALES ===
    st.subheader("📊 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_files = stats['scan_2']['files'] - stats['scan_1']['files']
        st.metric(
            "📄 Fichiers",
            f"{stats['scan_2']['files']:,}",
            delta=f"{delta_files:+,}",
            help="Évolution du nombre de fichiers"
        )
    
    with col2:
        delta_size = stats['scan_2']['size'] - stats['scan_1']['size']
        st.metric(
            "💾 Taille totale",
            format_size(stats['scan_2']['size']),
            delta=format_size(abs(delta_size)) + (" +" if delta_size >= 0 else " -"),
            help="Évolution de la taille totale"
        )
    
    with col3:
        st.metric(
            "🆕 Nouveaux",
            f"{stats['new_count']:,}",
            help="Fichiers ajoutés"
        )
    
    with col4:
        st.metric(
            "🗑️ Supprimés",
            f"{stats['deleted_count']:,}",
            help="Fichiers supprimés"
        )
    
    # === VISUALISATIONS ===
    st.markdown("---")
    st.subheader("📈 Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_evolution = create_evolution_chart(stats)
        st.plotly_chart(fig_evolution, use_container_width=True)
    
    with col2:
        fig_changes = create_changes_pie_chart(stats)
        st.plotly_chart(fig_changes, use_container_width=True)
    
    # === DÉTAILS ===
    st.markdown("---")
    
    # Tabs pour organiser
    tab1, tab2, tab3 = st.tabs(["🆕 Nouveaux fichiers", "🗑️ Fichiers supprimés", "✏️ Fichiers modifiés"])
    
    with tab1:
        df_new = comparison['new_files']
        if not df_new.empty:
            # Formater
            df_new['Taille'] = df_new['size_bytes'].apply(format_size)
            df_new['Date'] = df_new['mtime'].apply(format_timestamp)
            
            # Afficher
            st.caption(f"**{len(df_new):,} nouveaux fichiers** (top 1000 par taille)")
            st.dataframe(
                df_new[['name', 'Taille', 'owner', 'Date', 'path']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
            
            # Export
            csv = df_new.to_csv(index=False).encode('utf-8')
            st.download_button(
                "� Exporter CSV",
                data=csv,
                file_name="nouveaux_fichiers.csv",
                mime="text/csv"
            )
        else:
            st.info("Aucun nouveau fichier")
    
    with tab2:
        df_deleted = comparison['deleted_files']
        if not df_deleted.empty:
            # Formater
            df_deleted['Taille'] = df_deleted['size_bytes'].apply(format_size)
            df_deleted['Date'] = df_deleted['mtime'].apply(format_timestamp)
            
            st.caption(f"**{len(df_deleted):,} fichiers supprimés** (top 1000 par taille)")
            st.dataframe(
                df_deleted[['name', 'Taille', 'owner', 'Date', 'path']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
            
            # Export
            csv = df_deleted.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Exporter CSV",
                data=csv,
                file_name="fichiers_supprimes.csv",
                mime="text/csv"
            )
        else:
            st.info("Aucun fichier supprimé")
    
    with tab3:
        df_modified = comparison['modified_files']
        if not df_modified.empty:
            # Formater
            df_modified['Taille 1'] = df_modified['size_1'].apply(format_size)
            df_modified['Taille 2'] = df_modified['size_2'].apply(format_size)
            df_modified['Différence'] = df_modified['size_diff'].apply(
                lambda x: format_size(abs(x)) + (" +" if x >= 0 else " -")
            )
            
            st.caption(f"**{len(df_modified):,} fichiers modifiés** (top 1000 par différence)")
            st.dataframe(
                df_modified[['name', 'Taille 1', 'Taille 2', 'Différence', 'path']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
            
            # Export
            csv = df_modified.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Exporter CSV",
                data=csv,
                file_name="fichiers_modifies.csv",
                mime="text/csv"
            )
        else:
            st.info("Aucun fichier modifié")

# ============================================================================
# UI SÉLECTION
# ============================================================================

def select_scans_to_compare(db):
    """
    Interface de sélection de 2 scans.
    
    Args:
        db: DatabaseManager
        
    Returns:
        Tuple (scan_id_1, scan_id_2) ou None
    """
    st.subheader("🔍 Sélection des scans")
    
    # Récupérer scans disponibles
    df_scans = get_available_scans_for_comparison(db)
    
    if len(df_scans) < 2:
        st.warning("⚠️ Au moins 2 scans nécessaires pour comparaison")
        st.info("Lancez plusieurs scans avec `python scripts/run_scan.py`")
        return None
    
    # Formater options
    scan_options = {}
    for _, row in df_scans.iterrows():
        label = f"{row['scan_id']} - {row['date']} ({row['files']:,} fichiers, {row['size_formatted']})"
        scan_options[label] = row['scan_id']
    
    # Sélecteurs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Scan 1 (Base)**")
        selected_1 = st.selectbox(
            "Premier scan",
            options=list(scan_options.keys()),
            key='scan_1_selector',
            label_visibility='collapsed'
        )
        scan_id_1 = scan_options[selected_1]
        
        # Info scan 1
        info_1 = df_scans[df_scans['scan_id'] == scan_id_1].iloc[0]
        st.info(f"""
        **Date:** {info_1['date']}  
        **Fichiers:** {info_1['files']:,}  
        **Taille:** {info_1['size_formatted']}
        """)
    
    with col2:
        st.markdown("**📊 Scan 2 (Comparaison)**")
        selected_2 = st.selectbox(
            "Second scan",
            options=list(scan_options.keys()),
            key='scan_2_selector',
            label_visibility='collapsed'
        )
        scan_id_2 = scan_options[selected_2]
        
        # Info scan 2
        info_2 = df_scans[df_scans['scan_id'] == scan_id_2].iloc[0]
        st.info(f"""
        **Date:** {info_2['date']}  
        **Fichiers:** {info_2['files']:,}  
        **Taille:** {info_2['size_formatted']}
        """)
    
    # Vérifier que scans différents
    if scan_id_1 == scan_id_2:
        st.warning("⚠️ Veuillez sélectionner deux scans différents")
        return None
    
    return (scan_id_1, scan_id_2)

# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_comparisons(db):
    """
    Page principale de comparaisons.
    
    Args:
        db: DatabaseManager
    """
    st.title("🔄 Comparaisons de Scans")
    st.markdown("---")
    
    # Sélection scans
    scans = select_scans_to_compare(db)
    
    if not scans:
        return
    
    scan_id_1, scan_id_2 = scans
    
    # Bouton comparer
    st.markdown("---")
    if st.button("🔍 Lancer la comparaison", type="primary", use_container_width=True):
        st.session_state.comparison_active = True
        st.session_state.comparison_scans = (scan_id_1, scan_id_2)
        st.rerun()
    
    # Afficher résultats si comparaison active
    if st.session_state.get('comparison_active'):
        stored_scans = st.session_state.get('comparison_scans')
        if stored_scans == (scan_id_1, scan_id_2):
            st.markdown("---")
            
            with st.spinner("Calcul des différences..."):
                comparison = compute_comparison(db, scan_id_1, scan_id_2)
            
            display_comparison_results(comparison)
