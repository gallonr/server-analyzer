"""
Gestion centralisée des erreurs du dashboard.
Phase 3.3 - Module de gestion robuste des erreurs
"""

import streamlit as st
import logging
import traceback

logger = logging.getLogger('dashboard.errors')


def handle_database_error(e: Exception, context: str = ""):
    """
    Gère erreurs base de données.
    
    Args:
        e: Exception
        context: Contexte de l'erreur
    """
    logger.error(f"Database error in {context}: {e}")
    logger.error(traceback.format_exc())
    
    st.error(f"❌ Erreur d'accès à la base de données")
    st.error(f"**Contexte**: {context}")
    
    with st.expander("🔍 Détails techniques"):
        st.code(str(e))


def handle_query_error(e: Exception, query: str = ""):
    """
    Gère erreurs requêtes SQL.
    
    Args:
        e: Exception
        query: Requête SQL qui a échoué
    """
    logger.error(f"Query error: {e}")
    logger.error(f"Query: {query}")
    
    st.error("❌ Erreur lors de l'exécution de la requête")
    
    with st.expander("🔍 Détails"):
        st.code(f"Erreur: {e}\n\nRequête: {query}")


def handle_export_error(e: Exception, export_format: str):
    """
    Gère erreurs export.
    
    Args:
        e: Exception
        export_format: Format d'export (CSV, Excel, JSON)
    """
    logger.error(f"Export error ({export_format}): {e}")
    
    st.error(f"❌ Erreur lors de l'export {export_format}")
    st.info("Essayez avec moins de données ou un autre format")
    
    with st.expander("🔍 Détails"):
        st.code(str(e))


def handle_file_not_found_error(e: Exception, filepath: str = ""):
    """
    Gère erreurs fichier non trouvé.
    
    Args:
        e: Exception
        filepath: Chemin du fichier
    """
    logger.error(f"File not found: {filepath}: {e}")
    
    st.error(f"❌ Fichier non trouvé: `{filepath}`")
    st.info("Vérifiez que le fichier existe et que vous avez les droits d'accès")


def safe_execute(func, error_handler=None, *args, **kwargs):
    """
    Exécute fonction avec gestion erreur.
    
    Args:
        func: Fonction à exécuter
        error_handler: Fonction de gestion erreur custom
        *args, **kwargs: Arguments pour func
        
    Returns:
        Résultat de func ou None si erreur
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler(e)
        else:
            logger.error(f"Error in {func.__name__}: {e}")
            st.error(f"❌ Une erreur est survenue dans {func.__name__}")
            
            with st.expander("🔍 Détails techniques"):
                st.code(traceback.format_exc())
        
        return None


def check_database_connection(db):
    """
    Vérifie que la connexion base de données est active.
    
    Args:
        db: DatabaseManager
        
    Returns:
        bool: True si connexion OK
    """
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT 1")
        return True
    except Exception as e:
        handle_database_error(e, "Vérification connexion")
        return False


def validate_scan_id(db, scan_id: str):
    """
    Vérifie qu'un scan_id existe dans la base.
    
    Args:
        db: DatabaseManager
        scan_id: ID du scan
        
    Returns:
        bool: True si scan existe
    """
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scans WHERE id = ?", (scan_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            st.error(f"❌ Scan introuvable: `{scan_id}`")
            return False
        
        return True
        
    except Exception as e:
        handle_database_error(e, f"Validation scan_id {scan_id}")
        return False
