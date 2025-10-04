"""
Page Doublons - Détection et analyse de fichiers dupliqués.
Utilise le module duplicate_detector pour une détection multi-niveaux.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size, format_timestamp
from duplicate_detector import DuplicateDetector, get_duplicate_report

# ============================================================================
# DÉTECTION ET CACHE
# ============================================================================

@st.cache_data(ttl=600)
def detect_duplicates(_db, scan_id: str, min_size: int = 1024, num_workers: int = None,
                     use_cache: bool = True, save_to_cache: bool = True):
    """
    Lance la détection de doublons avec cache.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        min_size: Taille minimale en octets
        num_workers: Nombre de workers pour parallélisation
        use_cache: Utiliser le cache de la base de données si disponible
        save_to_cache: Sauvegarder les résultats dans le cache
        
    Returns:
        Rapport de doublons enrichi avec métadonnées
    """
    from duplicate_detector import DuplicateDetector
    
    detector = DuplicateDetector(_db.conn, scan_id, num_workers=num_workers)
    
    # Détection des doublons avec cache
    report = detector.detect_all_duplicates(
        min_size=min_size,
        use_cache=use_cache,
        save_to_cache=save_to_cache
    )
    
    # Enrichir les groupes avec métadonnées complètes
    if report['duplicate_groups']:
        enriched_groups = detector.get_duplicate_details(report['duplicate_groups'])
        report['duplicate_groups'] = enriched_groups
    
    return report


@st.cache_data(ttl=300)
def get_available_scans_for_duplicates(_db):
    """
    Récupère liste des scans disponibles.
    
    Args:
        _db: DatabaseManager
        
    Returns:
        DataFrame avec scans
    """
    cursor = _db.conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            start_time,
            total_files,
            total_size_bytes,
            status
        FROM scans
        WHERE status = 'completed'
        ORDER BY start_time DESC
    """)
    
    scans = []
    for row in cursor.fetchall():
        scans.append({
            'scan_id': row[0],
            'date': format_timestamp(row[1]),
            'files': row[2] or 0,
            'size': row[3] or 0,
            'size_formatted': format_size(row[3] or 0),
            'status': row[4]
        })
    
    return pd.DataFrame(scans)


# ============================================================================
# VISUALISATIONS
# ============================================================================

def create_duplicates_overview_chart(report: dict):
    """
    Graphique vue d'ensemble des doublons.
    
    Args:
        report: Rapport de détection
        
    Returns:
        Figure Plotly
    """
    fig = go.Figure()
    
    # Métriques
    labels = ['Fichiers uniques', 'Fichiers dupliqués']
    values = [
        report.get('total_groups', 0),  # Groupes = fichiers uniques
        report.get('total_duplicates', 0)  # Copies superflues
    ]
    
    colors = ['#28a745', '#dc3545']
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>%{value:,} fichiers<br>%{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribution fichiers uniques vs dupliqués",
        height=400,
        showlegend=True
    )
    
    return fig


def create_top_duplicates_chart(groups: list, top_n: int = 10):
    """
    Graphique des groupes de doublons les plus volumineux.
    
    Args:
        groups: Liste des groupes de doublons
        top_n: Nombre de groupes à afficher
        
    Returns:
        Figure Plotly
    """
    # Trier par espace gaspillé (taille × nombre de copies superflues)
    sorted_groups = sorted(
        groups,
        key=lambda g: g['size_bytes'] * (g['count'] - 1),
        reverse=True
    )[:top_n]
    
    # Préparer données
    labels = []
    wasted_space = []
    
    for i, group in enumerate(sorted_groups, 1):
        # Utiliser le premier path pour extraire le nom de fichier
        if 'files' in group and group['files']:
            filename = group['files'][0]['filename']
        elif 'paths' in group and group['paths']:
            from pathlib import Path
            filename = Path(group['paths'][0]).name
        else:
            filename = f"Group {i}"
        
        redundant = group['count'] - 1
        
        labels.append(f"{filename[:30]}... ({group['count']} copies)")
        wasted_space.append(group['size_bytes'] * redundant / (1024**3))  # GB
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=wasted_space,
        y=labels,
        orientation='h',
        marker_color='#ff6b6b',
        text=[f"{val:.2f} GB" for val in wasted_space],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>%{x:.2f} GB gaspillés<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} groupes - Espace gaspillé",
        xaxis_title="Espace gaspillé (GB)",
        yaxis_title="",
        height=400,
        showlegend=False
    )
    
    fig.update_yaxes(autorange="reversed")
    
    return fig


def create_size_distribution_chart(groups: list):
    """
    Distribution des tailles de groupes de doublons.
    
    Args:
        groups: Liste des groupes de doublons
        
    Returns:
        Figure Plotly
    """
    # Compter groupes par nombre de copies
    count_distribution = {}
    
    for group in groups:
        count = group['count']
        count_distribution[count] = count_distribution.get(count, 0) + 1
    
    # Trier par nombre de copies
    sorted_counts = sorted(count_distribution.items())
    
    labels = [f"{count} copies" for count, _ in sorted_counts]
    values = [freq for _, freq in sorted_counts]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker_color='#4ecdc4',
        text=values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>%{y} groupes<extra></extra>'
    ))
    
    fig.update_layout(
        title="Distribution par nombre de copies",
        xaxis_title="Nombre de copies",
        yaxis_title="Nombre de groupes",
        height=400,
        showlegend=False
    )
    
    return fig


# ============================================================================
# FILTRAGE DES GROUPES
# ============================================================================

def apply_duplicate_filters(groups: list) -> list:
    """
    Applique les filtres interactifs sur les groupes de doublons.
    
    Args:
        groups: Liste complète des groupes
        
    Returns:
        Liste filtrée des groupes
    """
    if not groups:
        return groups
    
    st.subheader("🔍 Filtres")
    
    # Extraire les propriétaires uniques
    all_owners = set()
    for group in groups:
        if 'files' in group:
            for file in group['files']:
                all_owners.add(file.get('owner', 'unknown'))
    
    all_owners = sorted(list(all_owners))
    
    # Interface de filtrage
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtre par propriétaire
        owner_filter = st.multiselect(
            "👤 Propriétaires",
            options=['Tous'] + all_owners,
            default=['Tous'],
            help="Filtrer par propriétaire des fichiers"
        )
    
    with col2:
        # Filtre par nombre de copies
        min_count = min(g['count'] for g in groups)
        max_count = max(g['count'] for g in groups)
        
        count_range = st.slider(
            "📋 Nombre de copies",
            min_value=int(min_count),
            max_value=int(max_count),
            value=(int(min_count), int(max_count)),
            help="Filtrer par nombre de copies"
        )
    
    with col3:
        # Filtre par taille de fichier
        min_size = min(g['size_bytes'] for g in groups)
        max_size = max(g['size_bytes'] for g in groups)
        
        # Convertir en MB pour l'interface
        min_size_mb = min_size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)
        
        size_range = st.slider(
            "💾 Taille fichier (MB)",
            min_value=float(min_size_mb),
            max_value=float(max_size_mb),
            value=(float(min_size_mb), float(max_size_mb)),
            format="%.2f",
            help="Filtrer par taille de fichier"
        )
    
    with col4:
        # Tri
        sort_by = st.selectbox(
            "📊 Trier par",
            options=[
                "Espace gaspillé (↓)",
                "Nombre de copies (↓)",
                "Taille fichier (↓)",
                "Nom fichier (↑)"
            ],
            help="Ordre de tri des résultats"
        )
    
    # Appliquer les filtres
    filtered_groups = []
    
    for group in groups:
        # Filtre par propriétaire
        if 'Tous' not in owner_filter:
            has_owner = False
            if 'files' in group:
                for file in group['files']:
                    if file.get('owner', 'unknown') in owner_filter:
                        has_owner = True
                        break
            if not has_owner:
                continue
        
        # Filtre par nombre de copies
        if not (count_range[0] <= group['count'] <= count_range[1]):
            continue
        
        # Filtre par taille (convertir MB en bytes)
        size_min_bytes = size_range[0] * 1024 * 1024
        size_max_bytes = size_range[1] * 1024 * 1024
        if not (size_min_bytes <= group['size_bytes'] <= size_max_bytes):
            continue
        
        filtered_groups.append(group)
    
    # Appliquer le tri
    if sort_by == "Espace gaspillé (↓)":
        filtered_groups.sort(
            key=lambda g: g['size_bytes'] * (g['count'] - 1),
            reverse=True
        )
    elif sort_by == "Nombre de copies (↓)":
        filtered_groups.sort(key=lambda g: g['count'], reverse=True)
    elif sort_by == "Taille fichier (↓)":
        filtered_groups.sort(key=lambda g: g['size_bytes'], reverse=True)
    elif sort_by == "Nom fichier (↑)":
        filtered_groups.sort(
            key=lambda g: g['files'][0]['filename'] if 'files' in g and g['files'] else ''
        )
    
    # Afficher info de filtrage
    st.info(
        f"📊 **{len(filtered_groups)}** groupes affichés "
        f"sur **{len(groups)}** au total"
    )
    
    return filtered_groups


# ============================================================================
# AFFICHAGE RÉSULTATS
# ============================================================================

def display_duplicate_stats(report: dict):
    """
    Affiche statistiques globales de doublons.
    
    Args:
        report: Rapport de détection
    """
    st.subheader("📊 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🔍 Groupes détectés",
            f"{report['total_groups']:,}",
            help="Nombre de fichiers uniques ayant des doublons"
        )
    
    with col2:
        st.metric(
            "📋 Fichiers dupliqués",
            f"{report['total_duplicates']:,}",
            help="Nombre total de copies superflues"
        )
    
    with col3:
        wasted_gb = report['wasted_space'] / (1024**3)
        st.metric(
            "💾 Espace gaspillé",
            f"{wasted_gb:.2f} GB",
            help="Espace disque occupé par les doublons"
        )
    
    with col4:
        st.metric(
            "⏱️ Temps d'analyse",
            f"{report['execution_time']:.1f}s",
            help="Durée de la détection"
        )


def display_duplicate_groups(groups: list, page_size: int = 20):
    """
    Affiche les groupes de doublons avec pagination.
    
    Args:
        groups: Liste des groupes enrichis (déjà filtrés et triés)
        page_size: Nombre de groupes par page
    """
    if not groups:
        st.info("✅ Aucun doublon détecté (ou tous filtrés)")
        return
    
    st.subheader(f"📁 Groupes de doublons")
    
    # Pagination
    total_pages = (len(groups) + page_size - 1) // page_size
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, total_pages),
            value=1,
            step=1,
            key="duplicate_page"
        )
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(groups))
    
    st.info(f"Affichage groupes {start_idx + 1} à {end_idx} sur {len(groups)}")
    
    # Afficher groupes de la page courante
    for i, group in enumerate(groups[start_idx:end_idx], start=start_idx + 1):
        redundant = group['count'] - 1
        wasted = group['size_bytes'] * redundant
        
        with st.expander(
            f"**Groupe {i}** - {group['files'][0]['filename'][:50]} "
            f"({group['count']} copies, {format_size(wasted)} gaspillés)",
            expanded=(i == start_idx + 1)  # Premier groupe ouvert
        ):
            # Info groupe
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Taille fichier", format_size(group['size_bytes']))
            with col2:
                st.metric("Nombre de copies", group['count'])
            with col3:
                st.metric("Espace gaspillé", format_size(wasted))
            
            st.markdown("---")
            
            # Hash pour vérification
            st.code(f"Hash MD5: {group['hash']}", language="text")
            
            # Liste des fichiers
            st.markdown("**📄 Fichiers du groupe:**")
            
            files_data = []
            for idx, file in enumerate(group['files']):
                is_oldest = (idx == 0)  # Premier = le plus ancien
                
                files_data.append({
                    '#': idx + 1,
                    'Original': '⭐' if is_oldest else '',
                    'Chemin': file['path'],
                    'Propriétaire': file['owner'],
                    'Date modif': format_timestamp(file['mtime']),
                    'Permissions': file['permissions']
                })
            
            df = pd.DataFrame(files_data)
            
            # Afficher avec style
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export CSV du groupe
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Exporter ce groupe (CSV)",
                data=csv,
                file_name=f"groupe_doublons_{i}.csv",
                mime="text/csv",
                key=f"export_group_{i}"
            )


def display_visualizations(report: dict):
    """
    Affiche les graphiques de visualisation.
    
    Args:
        report: Rapport de détection
    """
    st.subheader("📈 Visualisations")
    
    groups = report.get('duplicate_groups', [])
    
    if not groups:
        st.info("Aucun doublon à visualiser")
        return
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Vue d'ensemble",
        "🏆 Top groupes",
        "📦 Distribution"
    ])
    
    with tab1:
        fig = create_duplicates_overview_chart(report)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_top_duplicates_chart(groups, top_n=15)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = create_size_distribution_chart(groups)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# SÉLECTION SCAN
# ============================================================================

def select_scan_for_duplicates(db):
    """
    Sélecteur de scan pour analyse doublons.
    
    Args:
        db: DatabaseManager
        
    Returns:
        ID du scan sélectionné ou None
    """
    df_scans = get_available_scans_for_duplicates(db)
    
    if df_scans.empty:
        st.warning("⚠️ Aucun scan disponible pour analyse")
        return None
    
    st.subheader("🎯 Sélection du scan")
    
    # Options pour dropdown
    scan_options = {
        f"{row['scan_id'][:8]}... - {row['date']} ({row['files']:,} fichiers, {row['size_formatted']})": 
        row['scan_id']
        for _, row in df_scans.iterrows()
    }
    
    selected = st.selectbox(
        "Choisir un scan",
        options=list(scan_options.keys()),
        key="duplicate_scan_select",
        help="Sélectionnez le scan à analyser pour détecter les doublons"
    )
    
    scan_id = scan_options[selected]
    
    # Info scan
    info = df_scans[df_scans['scan_id'] == scan_id].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📅 **Date:** {info['date']}")
    with col2:
        st.info(f"📄 **Fichiers:** {info['files']:,}")
    with col3:
        st.info(f"💾 **Taille:** {info['size_formatted']}")
    
    return scan_id


# ============================================================================
# CONFIGURATION DÉTECTION
# ============================================================================

def get_detection_config():
    """
    Interface de configuration de la détection.
    
    Returns:
        Dict avec paramètres de détection
    """
    st.subheader("⚙️ Configuration de la détection")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_size_kb = st.number_input(
            "Taille minimale (KB)",
            min_value=0,
            max_value=10240,  # 10 MB
            value=1,  # 1 KB par défaut
            step=1,
            help="Ignorer les fichiers plus petits que cette taille"
        )
    
    with col2:
        import multiprocessing
        max_workers = multiprocessing.cpu_count()
        
        num_workers = st.number_input(
            "Nombre de workers",
            min_value=1,
            max_value=max_workers,
            value=max(1, max_workers - 1),
            step=1,
            help=f"Nombre de processus parallèles pour le calcul des hash (max: {max_workers})"
        )
    
    with col3:
        use_cache = st.checkbox(
            "Utiliser le cache",
            value=True,
            help="Réutiliser les résultats précédents si disponibles"
        )
    
    # Info sur la parallélisation
    st.info(
        f"💡 **Mode parallélisé activé** : {num_workers} workers seront utilisés pour "
        f"calculer les hash MD5 simultanément. Cela peut accélérer significativement "
        f"la détection sur les gros volumes de données."
    )
    
    return {
        'min_size': min_size_kb * 1024,  # Convertir en bytes
        'num_workers': num_workers,
        'use_cache': use_cache
    }


# ============================================================================
# EXPORTS
# ============================================================================

def export_duplicate_report(report: dict, scan_id: str):
    """
    Génère exports du rapport de doublons.
    
    Args:
        report: Rapport de détection
        scan_id: ID du scan
    """
    st.subheader("💾 Exports")
    
    groups = report.get('duplicate_groups', [])
    
    if not groups:
        st.info("Aucun doublon à exporter")
        return
    
    # Préparer données pour export
    export_data = []
    
    for i, group in enumerate(groups, 1):
        for idx, file in enumerate(group['files']):
            is_original = (idx == 0)
            redundant = group['count'] - 1
            wasted = group['size_bytes'] * redundant if not is_original else 0
            
            export_data.append({
                'Groupe': i,
                'Hash': group['hash'],
                'Original': 'Oui' if is_original else 'Non',
                'Chemin': file['path'],
                'Nom_fichier': file['filename'],
                'Taille_bytes': group['size_bytes'],
                'Taille_formatée': format_size(group['size_bytes']),
                'Propriétaire': file['owner'],
                'Date_modification': format_timestamp(file['mtime']),
                'Permissions': file['permissions'],
                'Répertoire_parent': file['parent_dir'],
                'Copies_total': group['count'],
                'Espace_gaspillé_bytes': wasted
            })
    
    df_export = pd.DataFrame(export_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export CSV
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📊 Exporter CSV complet",
            data=csv,
            file_name=f"doublons_{scan_id[:8]}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export résumé
        summary_data = []
        for i, group in enumerate(groups, 1):
            redundant = group['count'] - 1
            wasted = group['size_bytes'] * redundant
            
            summary_data.append({
                'Groupe': i,
                'Fichier': group['files'][0]['filename'],
                'Taille': format_size(group['size_bytes']),
                'Copies': group['count'],
                'Espace_gaspillé': format_size(wasted),
                'Hash': group['hash']
            })
        
        df_summary = pd.DataFrame(summary_data)
        csv_summary = df_summary.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📋 Exporter résumé (CSV)",
            data=csv_summary,
            file_name=f"doublons_resume_{scan_id[:8]}.csv",
            mime="text/csv"
        )


# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_duplicates(db):
    """
    Page principale de détection de doublons.
    
    Args:
        db: DatabaseManager
    """
    st.title("🔍 Détection de Doublons")
    
    st.markdown("""
    Cette page permet de détecter les fichiers dupliqués en utilisant une analyse multi-niveaux :
    1. **Regroupement par taille** - Fichiers de même taille
    2. **Hash partiel** - Vérification des premiers KB
    3. **Hash complet** - Validation finale MD5
    """)
    
    st.markdown("---")
    
    # Sélection scan
    scan_id = select_scan_for_duplicates(db)
    
    if not scan_id:
        return
    
    st.markdown("---")
    
    # Configuration
    config = get_detection_config()
    
    st.markdown("---")
    
    # Bouton lancer détection
    if st.button("🚀 Lancer la détection", type="primary", use_container_width=True):
        st.session_state.duplicate_detection_active = True
        st.session_state.duplicate_scan_id = scan_id
        st.session_state.duplicate_config = config
        st.rerun()
    
    # Afficher résultats si détection lancée
    if st.session_state.get('duplicate_detection_active'):
        stored_scan = st.session_state.get('duplicate_scan_id')
        stored_config = st.session_state.get('duplicate_config', {})
        
        if stored_scan == scan_id:
            st.markdown("---")
            
            with st.spinner("🔍 Détection en cours... Cela peut prendre quelques minutes."):
                # Lancer détection
                report = detect_duplicates(
                    db,
                    scan_id,
                    min_size=stored_config.get('min_size', 1024),
                    num_workers=stored_config.get('num_workers'),
                    use_cache=True,
                    save_to_cache=True
                )
            
            # Afficher résultats avec statut cache
            if report.get('from_cache', False):
                st.success(f"⚡ Résultats récupérés depuis le cache en {report['execution_time']:.3f}s (gain de temps!)")
            else:
                st.success(f"✅ Détection terminée en {report['execution_time']:.1f}s (résultats sauvegardés dans le cache)")
            
            st.markdown("---")
            
            # Statistiques
            display_duplicate_stats(report)
            
            st.markdown("---")
            
            # Visualisations
            display_visualizations(report)
            
            st.markdown("---")
            
            # Filtres interactifs
            groups = report.get('duplicate_groups', [])
            if groups:
                filtered_groups = apply_duplicate_filters(groups)
            else:
                filtered_groups = []
            
            st.markdown("---")
            
            # Liste détaillée (groupes filtrés)
            display_duplicate_groups(filtered_groups)
            
            st.markdown("---")
            
            # Exports (sur groupes filtrés)
            export_duplicate_report({'duplicate_groups': filtered_groups}, scan_id)
            
            # Bouton réinitialiser
            if st.button("🔄 Nouvelle détection", use_container_width=True):
                st.session_state.duplicate_detection_active = False
                st.rerun()
