"""
Module d'optimisation et monitoring des performances du dashboard.
Phase 3.3 - Optimisations mineures
"""

import time
import logging
import streamlit as st
from functools import wraps

logger = logging.getLogger('dashboard.performance')

# ============================================================================
# PROFILING REQUÊTES SQL
# ============================================================================

def profile_query(func):
    """
    Décorateur pour profiler les requêtes SQL.
    Affiche un warning si la requête prend > 1s.
    
    Usage:
        @profile_query
        def my_query_function(db, ...):
            # ... requête SQL
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        # Log si lent
        if duration > 1.0:
            logger.warning(f"⚠️ Requête lente: {func.__name__} ({duration:.2f}s)")
            if st.session_state.get('show_performance_warnings', False):
                st.warning(f"⚠️ Requête lente: {func.__name__} ({duration:.2f}s)")
        
        # Log debug toujours
        logger.debug(f"Query {func.__name__}: {duration:.3f}s")
        
        return result
    
    return wrapper


def measure_time(operation_name: str):
    """
    Context manager pour mesurer le temps d'une opération.
    
    Usage:
        with measure_time("Chargement données"):
            # ... opération longue
    """
    class TimeMeasure:
        def __enter__(self):
            self.start = time.time()
            return self
        
        def __exit__(self, *args):
            duration = time.time() - self.start
            logger.info(f"{operation_name}: {duration:.3f}s")
            
            if duration > 2.0:
                logger.warning(f"⚠️ Opération lente: {operation_name} ({duration:.2f}s)")
    
    return TimeMeasure()


# ============================================================================
# VÉRIFICATION INDEX SQL
# ============================================================================

@st.cache_data(ttl=3600)
def check_database_indexes(_db):
    """
    Vérifie que tous les index nécessaires sont présents.
    
    Args:
        _db: DatabaseManager
        
    Returns:
        dict: {index_name: exists}
    """
    cursor = _db.conn.cursor()
    
    # Récupérer index existants
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index'
        AND name NOT LIKE 'sqlite_%'
    """)
    
    existing_indexes = {row[0] for row in cursor.fetchall()}
    
    # Index requis
    required_indexes = {
        'idx_scan_id',
        'idx_parent_dir',
        'idx_extension',
        'idx_owner_name',
        'idx_size_bytes',
        'idx_mtime',
        'idx_is_directory'
    }
    
    results = {}
    missing = []
    
    for idx in required_indexes:
        exists = idx in existing_indexes
        results[idx] = exists
        if not exists:
            missing.append(idx)
    
    # Afficher warning si manquants
    if missing:
        logger.warning(f"Index manquants: {', '.join(missing)}")
        st.warning(f"⚠️ Index SQL manquants: {', '.join(missing)}\n\nPerformance peut être dégradée.")
    
    return results


def analyze_query_plan(_db, query: str, params: tuple = ()):
    """
    Analyse le plan d'exécution d'une requête SQL.
    Utile pour debugging performance.
    
    Args:
        _db: DatabaseManager
        query: Requête SQL
        params: Paramètres requête
        
    Returns:
        list: Plan d'exécution
    """
    cursor = _db.conn.cursor()
    
    explain_query = f"EXPLAIN QUERY PLAN {query}"
    cursor.execute(explain_query, params)
    
    plan = cursor.fetchall()
    
    logger.debug(f"Query plan for: {query[:100]}...")
    for row in plan:
        logger.debug(f"  {row}")
    
    return plan


# ============================================================================
# OPTIMISATION CACHE
# ============================================================================

def get_optimal_ttl(data_type: str) -> int:
    """
    Retourne le TTL optimal selon le type de données.
    
    Args:
        data_type: Type de données ('static', 'semi_static', 'dynamic')
        
    Returns:
        int: TTL en secondes
    """
    ttl_mapping = {
        'static': 3600,      # 1h - données qui changent rarement (scan info)
        'semi_static': 600,  # 10min - stats agrégées
        'dynamic': 60,       # 1min - données filtrées
        'realtime': 0        # Pas de cache
    }
    
    return ttl_mapping.get(data_type, 300)  # Default 5min


def clear_all_caches():
    """
    Vide tous les caches Streamlit.
    Utile après modification données.
    """
    st.cache_data.clear()
    logger.info("Tous les caches ont été vidés")
    st.success("✅ Caches vidés")


# ============================================================================
# MONITORING PERFORMANCE
# ============================================================================

class PerformanceMonitor:
    """
    Moniteur de performance pour le dashboard.
    """
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, operation: str, duration: float):
        """Enregistre une métrique."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
    
    def get_stats(self, operation: str) -> dict:
        """Récupère statistiques pour une opération."""
        if operation not in self.metrics:
            return {}
        
        durations = self.metrics[operation]
        return {
            'count': len(durations),
            'avg': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations),
            'total': sum(durations)
        }
    
    def display_stats(self):
        """Affiche les statistiques dans Streamlit."""
        if not self.metrics:
            st.info("Aucune métrique enregistrée")
            return
        
        st.subheader("📊 Performance Metrics")
        
        for operation, durations in self.metrics.items():
            stats = self.get_stats(operation)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Opération", operation)
            with col2:
                st.metric("Moyenne", f"{stats['avg']:.3f}s")
            with col3:
                st.metric("Min/Max", f"{stats['min']:.3f}s / {stats['max']:.3f}s")
            with col4:
                st.metric("Appels", stats['count'])


# Instance globale
_monitor = PerformanceMonitor()

def get_monitor():
    """Retourne l'instance du moniteur."""
    return _monitor
