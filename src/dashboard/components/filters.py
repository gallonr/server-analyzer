"""
Composants de filtrage dynamique pour le dashboard.
"""

import streamlit as st
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils import format_size

# ============================================================================
# RÉCUPÉRATION OPTIONS FILTRES
# ============================================================================

@st.cache_data(ttl=300)
def get_filter_options(_db, scan_id: str):
    """
    Récupère options disponibles pour filtres.
    
    Args:
        _db: DatabaseManager
        scan_id: ID du scan
        
    Returns:
        Dict avec listes d'options
    """
    cursor = _db.conn.cursor()
    
    # Extensions disponibles
    cursor.execute("""
        SELECT DISTINCT extension
        FROM files
        WHERE scan_id = ?
        ORDER BY extension
    """, (scan_id,))
    extensions = [row[0] or 'no_ext' for row in cursor.fetchall()]
    
    # Propriétaires disponibles
    cursor.execute("""
        SELECT DISTINCT owner_name
        FROM files
        WHERE scan_id = ?
        ORDER BY owner_name
    """, (scan_id,))
    owners = [row[0] or 'unknown' for row in cursor.fetchall()]
    
    # Plage tailles
    cursor.execute("""
        SELECT MIN(size_bytes), MAX(size_bytes)
        FROM files
        WHERE scan_id = ?
    """, (scan_id,))
    min_size, max_size = cursor.fetchone()
    
    # Plage dates
    cursor.execute("""
        SELECT MIN(mtime), MAX(mtime)
        FROM files
        WHERE scan_id = ?
    """, (scan_id,))
    min_date, max_date = cursor.fetchone()
    
    return {
        'extensions': extensions,
        'owners': owners,
        'min_size': min_size or 0,
        'max_size': max_size or 0,
        'min_date': min_date or int((datetime.now() - timedelta(days=365)).timestamp()),
        'max_date': max_date or int(datetime.now().timestamp())
    }

# ============================================================================
# COMPOSANT FILTRES SIDEBAR
# ============================================================================

def render_filters_sidebar(db, scan_id: str):
    """
    Affiche filtres dans sidebar.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        
    Returns:
        Dict avec filtres actifs
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtres")
    
    # Récupérer options
    options = get_filter_options(db, scan_id)
    
    # Initialiser session state pour filtres
    if 'filters_active' not in st.session_state:
        st.session_state.filters_active = False
    
    filters = {}
    
    # === FILTRE TAILLE ===
    with st.sidebar.expander("💾 Taille fichier", expanded=False):
        size_filter_enabled = st.checkbox("Activer filtre taille", key='size_filter_enabled')
        
        if size_filter_enabled:
            min_size_mb = st.number_input(
                "Taille minimale (MB)",
                min_value=0.0,
                max_value=float(options['max_size']) / (1024**2),
                value=0.0,
                step=1.0,
                key='min_size_mb'
            )
            
            max_size_mb = st.number_input(
                "Taille maximale (MB)",
                min_value=0.0,
                max_value=float(options['max_size']) / (1024**2),
                value=float(options['max_size']) / (1024**2),
                step=1.0,
                key='max_size_mb'
            )
            
            filters['size_min'] = int(min_size_mb * 1024 * 1024)
            filters['size_max'] = int(max_size_mb * 1024 * 1024)
    
    # === FILTRE EXTENSION ===
    with st.sidebar.expander("📄 Extension", expanded=False):
        ext_filter_enabled = st.checkbox("Activer filtre extension", key='ext_filter_enabled')
        
        if ext_filter_enabled:
            selected_extensions = st.multiselect(
                "Extensions",
                options=options['extensions'],
                default=[],
                key='selected_extensions'
            )
            
            if selected_extensions:
                filters['extensions'] = selected_extensions
    
    # === FILTRE PROPRIÉTAIRE ===
    with st.sidebar.expander("👤 Propriétaire", expanded=False):
        owner_filter_enabled = st.checkbox("Activer filtre propriétaire", key='owner_filter_enabled')
        
        if owner_filter_enabled:
            selected_owners = st.multiselect(
                "Propriétaires",
                options=options['owners'],
                default=[],
                key='selected_owners'
            )
            
            if selected_owners:
                filters['owners'] = selected_owners
    
    # === FILTRE DATE MODIFICATION ===
    with st.sidebar.expander("📅 Date modification", expanded=False):
        date_filter_enabled = st.checkbox("Activer filtre date", key='date_filter_enabled')
        
        if date_filter_enabled:
            # Convertir timestamps en dates
            min_date_obj = datetime.fromtimestamp(options['min_date'])
            max_date_obj = datetime.fromtimestamp(options['max_date'])
            
            date_range = st.date_input(
                "Période",
                value=(min_date_obj.date(), max_date_obj.date()),
                min_value=min_date_obj.date(),
                max_value=max_date_obj.date(),
                key='date_range'
            )
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                filters['date_min'] = int(datetime.combine(date_range[0], datetime.min.time()).timestamp())
                filters['date_max'] = int(datetime.combine(date_range[1], datetime.max.time()).timestamp())
    
    # === FILTRE NOM FICHIER ===
    with st.sidebar.expander("🔤 Nom fichier", expanded=False):
        name_filter_enabled = st.checkbox("Activer filtre nom", key='name_filter_enabled')
        
        if name_filter_enabled:
            name_pattern = st.text_input(
                "Rechercher dans le nom",
                placeholder="ex: rapport, *.pdf, data_*",
                key='name_pattern'
            )
            
            if name_pattern:
                filters['name_pattern'] = name_pattern
    
    # === BOUTONS ACTION ===
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("✅ Appliquer", key='apply_filters', use_container_width=True):
            st.session_state.filters_active = True
            st.session_state.current_filters = filters.copy()
            st.rerun()
    
    with col2:
        if st.button("🔄 Réinitialiser", key='reset_filters', use_container_width=True):
            st.session_state.filters_active = False
            st.session_state.current_filters = {}
            # Réinitialiser les valeurs des filtres
            for key in list(st.session_state.keys()):
                if key.endswith('_enabled') or key.startswith('selected_') or key == 'name_pattern':
                    del st.session_state[key]
            st.rerun()
    
    # Afficher filtres actifs
    if st.session_state.filters_active and st.session_state.get('current_filters'):
        active = st.session_state.current_filters
        st.sidebar.markdown("---")
        st.sidebar.caption("**Filtres actifs:**")
        
        filter_count = 0
        if 'size_min' in active or 'size_max' in active:
            st.sidebar.caption(f"• Taille: {format_size(active.get('size_min', 0))} - {format_size(active.get('size_max', 0))}")
            filter_count += 1
        if 'extensions' in active:
            st.sidebar.caption(f"• Extensions: {len(active['extensions'])} sélectionnées")
            filter_count += 1
        if 'owners' in active:
            st.sidebar.caption(f"• Propriétaires: {len(active['owners'])} sélectionnés")
            filter_count += 1
        if 'date_min' in active or 'date_max' in active:
            st.sidebar.caption("• Dates: période personnalisée")
            filter_count += 1
        if 'name_pattern' in active:
            st.sidebar.caption(f"• Nom: *{active['name_pattern']}*")
            filter_count += 1
        
        st.sidebar.success(f"🎯 {filter_count} filtre(s) actif(s)")
    
    return st.session_state.get('current_filters', {})

# ============================================================================
# APPLICATION FILTRES
# ============================================================================

def apply_filters_to_query(base_query: str, filters: dict, params: list):
    """
    Applique filtres à une requête SQL.
    
    Args:
        base_query: Requête SQL de base
        filters: Dictionnaire de filtres
        params: Liste de paramètres (modifiée in-place)
        
    Returns:
        Requête SQL modifiée
    """
    conditions = []
    
    # Filtre taille
    if 'size_min' in filters:
        conditions.append("size_bytes >= ?")
        params.append(filters['size_min'])
    
    if 'size_max' in filters:
        conditions.append("size_bytes <= ?")
        params.append(filters['size_max'])
    
    # Filtre extensions
    if 'extensions' in filters and filters['extensions']:
        placeholders = ','.join('?' * len(filters['extensions']))
        conditions.append(f"extension IN ({placeholders})")
        params.extend(filters['extensions'])
    
    # Filtre propriétaires
    if 'owners' in filters and filters['owners']:
        placeholders = ','.join('?' * len(filters['owners']))
        conditions.append(f"owner_name IN ({placeholders})")
        params.extend(filters['owners'])
    
    # Filtre date
    if 'date_min' in filters:
        conditions.append("mtime >= ?")
        params.append(filters['date_min'])
    
    if 'date_max' in filters:
        conditions.append("mtime <= ?")
        params.append(filters['date_max'])
    
    # Filtre nom
    if 'name_pattern' in filters:
        conditions.append("name LIKE ?")
        params.append(f"%{filters['name_pattern']}%")
    
    # Ajouter conditions à requête
    if conditions:
        if 'WHERE' in base_query:
            query = base_query + " AND " + " AND ".join(conditions)
        else:
            query = base_query + " WHERE " + " AND ".join(conditions)
    else:
        query = base_query
    
    return query
