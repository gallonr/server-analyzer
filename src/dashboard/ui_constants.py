"""
Constantes UI et design pour le dashboard.
Phase 3.3 - Optimisations UX
"""

# ============================================================================
# ICONS COHÉRENTS
# ============================================================================

ICONS = {
    # Navigation
    'home': '🏠',
    'overview': '📊',
    'explorer': '🔍',
    'comparisons': '🔄',
    'exports': '💾',
    'settings': '⚙️',
    
    # Fichiers et dossiers
    'file': '📄',
    'folder': '📁',
    'folder_open': '📂',
    
    # Données
    'size': '💾',
    'volume': '📦',
    'count': '🔢',
    
    # Temps
    'time': '⏱️',
    'date': '📅',
    'clock': '🕐',
    'calendar': '📆',
    
    # Utilisateurs
    'user': '👤',
    'users': '👥',
    'owner': '🔑',
    'group': '👨‍👩‍👧‍👦',
    
    # Actions
    'download': '⬇️',
    'upload': '⬆️',
    'refresh': '🔄',
    'search': '🔍',
    'filter': '🔽',
    'sort': '↕️',
    'edit': '✏️',
    'delete': '🗑️',
    'add': '➕',
    'remove': '➖',
    
    # État
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'question': '❓',
    'tip': '💡',
    
    # Graphiques
    'chart_bar': '📊',
    'chart_pie': '🥧',
    'chart_line': '📈',
    'chart_area': '📉',
    'treemap': '🗺️',
    
    # Comparaison
    'new': '🆕',
    'deleted': '🗑️',
    'modified': '✏️',
    'unchanged': '➖',
    'diff': '🔀',
    
    # Formats
    'csv': '📄',
    'excel': '📊',
    'json': '📋',
    'pdf': '📕',
    
    # Divers
    'rocket': '🚀',
    'fire': '🔥',
    'star': '⭐',
    'trophy': '🏆',
    'target': '🎯',
    'tools': '🔧',
    'database': '🗄️',
    'lock': '🔒',
    'unlock': '🔓',
}


def get_icon(name: str, default: str = '•') -> str:
    """
    Récupère un icon par nom.
    
    Args:
        name: Nom de l'icon
        default: Icon par défaut si non trouvé
        
    Returns:
        str: Icon emoji
    """
    return ICONS.get(name, default)


# ============================================================================
# MESSAGES D'AIDE
# ============================================================================

HELP_MESSAGES = {
    'overview': """
    ### 📊 Vue d'ensemble
    
    Cette page affiche les statistiques globales de votre scan :
    
    - **Métriques** : Nombre total de fichiers, volume total, etc.
    - **Top Extensions** : Les types de fichiers les plus présents
    - **Top Propriétaires** : Les utilisateurs qui possèdent le plus de données
    - **Visualisations** : Graphiques interactifs (Pie chart, Treemap, Timeline)
    
    💡 **Astuce** : Cliquez sur "🔄 Actualiser" pour rafraîchir les données.
    """,
    
    'explorer': """
    ### 🔍 Explorateur
    
    Naviguez dans l'arborescence du serveur :
    
    - **Navigation** : Cliquez sur un dossier pour voir son contenu
    - **Breadcrumb** : Utilisez le fil d'ariane pour remonter
    - **Tableau** : Liste complète des fichiers avec tri et pagination
    - **Export** : Téléchargez les données en CSV
    
    💡 **Astuce** : Utilisez les filtres (sidebar) pour affiner votre recherche.
    """,
    
    'filters': """
    ### 🔽 Filtres
    
    Affinez votre recherche avec les filtres :
    
    - **Taille** : Plage min/max en MB
    - **Extension** : Types de fichiers (.txt, .pdf, etc.)
    - **Propriétaire** : Nom d'utilisateur
    - **Date** : Période de modification
    - **Nom** : Pattern de recherche
    
    💡 **Actions** :
    - Cliquez "✅ Appliquer" pour filtrer
    - Cliquez "🔄 Réinitialiser" pour effacer
    """,
    
    'comparisons': """
    ### 🔄 Comparaisons
    
    Comparez deux scans pour voir l'évolution :
    
    - **Sélection** : Choisissez 2 scans différents
    - **Nouveaux** : Fichiers ajoutés depuis le scan 1
    - **Supprimés** : Fichiers retirés
    - **Modifiés** : Fichiers dont la taille/date a changé
    - **Graphiques** : Évolution visuelle
    
    💡 **Astuce** : Lancez régulièrement des scans pour suivre l'évolution.
    """,
    
    'exports': """
    ### 💾 Exports
    
    Exportez les données dans différents formats :
    
    - **CSV** : Format universel, compatible Excel
    - **Excel** : Multi-feuilles avec formatage
    - **JSON** : Format structuré pour scripts
    
    💡 **Options** :
    - Cochez "Appliquer filtres" pour exporter seulement les données filtrées
    - Ajustez le nombre max de lignes
    """,
    
    'scan_info': """
    ### 📋 Informations du Scan
    
    - **Scan ID** : Identifiant unique du scan
    - **Date** : Date et heure d'exécution
    - **Durée** : Temps total du scan
    - **Fichiers** : Nombre total de fichiers analysés
    - **Volume** : Taille totale des données
    """,
    
    'file_table': """
    ### 📄 Tableau des Fichiers
    
    - **Tri** : Cliquez sur les en-têtes pour trier
    - **Pagination** : Naviguez entre les pages (bas du tableau)
    - **Export** : Téléchargez la page courante ou tout
    
    💡 **Colonnes** :
    - **Nom** : Nom du fichier
    - **Taille** : Taille formatée (KB, MB, GB)
    - **Propriétaire** : Utilisateur propriétaire
    - **Date** : Dernière modification
    - **Chemin** : Chemin complet
    """,
}


def get_help(topic: str, default: str = "Aucune aide disponible") -> str:
    """
    Récupère un message d'aide.
    
    Args:
        topic: Sujet d'aide
        default: Message par défaut
        
    Returns:
        str: Message d'aide
    """
    return HELP_MESSAGES.get(topic, default)


# ============================================================================
# TOOLTIPS
# ============================================================================

TOOLTIPS = {
    # Métriques Overview
    'total_files': "📖 Nombre total de fichiers scannés dans l'arborescence (hors dossiers)",
    'total_size': "📖 Volume total des données en octets (taille cumulée de tous les fichiers)",
    'total_dirs': "📖 Nombre de dossiers dans l'arborescence",
    'scan_duration': "📖 Temps écoulé entre le début et la fin du scan",
    
    # Filtres
    'size_min': "📖 Taille minimale des fichiers en MB (1 MB = 1,000,000 octets)",
    'size_max': "📖 Taille maximale des fichiers en MB",
    'extension': "📖 Extension du fichier (ex: .txt, .pdf, .jpg)",
    'owner': "📖 Nom d'utilisateur propriétaire du fichier",
    'date_from': "📖 Date de modification minimale (fichiers modifiés après)",
    'date_to': "📖 Date de modification maximale (fichiers modifiés avant)",
    'name_pattern': "📖 Pattern de recherche dans le nom du fichier (case-insensitive)",
    
    # Comparaisons
    'scan_1': "📖 Scan de référence (base de comparaison)",
    'scan_2': "📖 Scan à comparer avec le scan de référence",
    'new_files': "📖 Fichiers présents dans le scan 2 mais absents du scan 1",
    'deleted_files': "📖 Fichiers présents dans le scan 1 mais absents du scan 2",
    'modified_files': "📖 Fichiers présents dans les deux scans mais avec taille/date différente",
    
    # Exports
    'export_format': "📖 Format du fichier d'export",
    'apply_filters': "📖 Si activé, seuls les fichiers filtrés seront exportés",
    'max_rows': "📖 Nombre maximum de fichiers à exporter (limite la taille du fichier)",
    
    # Performance
    'cache_ttl': "📖 Durée de vie du cache en secondes (données gardées en mémoire)",
    'batch_size': "📖 Nombre d'éléments traités par lot",
}


def get_tooltip(key: str, default: str = None) -> str:
    """
    Récupère un tooltip.
    
    Args:
        key: Clé du tooltip
        default: Tooltip par défaut
        
    Returns:
        str: Tooltip
    """
    return TOOLTIPS.get(key, default)


# ============================================================================
# COULEURS ET THÈME
# ============================================================================

COLORS = {
    'primary': '#4472C4',      # Bleu principal
    'secondary': '#70AD47',    # Vert
    'danger': '#E74C3C',       # Rouge
    'warning': '#F39C12',      # Orange
    'info': '#3498DB',         # Bleu clair
    'success': '#2ECC71',      # Vert clair
    'neutral': '#95A5A6',      # Gris
}


COLOR_SCHEMES = {
    'extensions': ['#4472C4', '#70AD47', '#FFC000', '#5B9BD5', '#ED7D31', '#A5A5A5', '#264478', '#9E480E'],
    'comparison': {
        'new': '#2ECC71',      # Vert
        'deleted': '#E74C3C',  # Rouge
        'modified': '#F39C12', # Orange
    }
}


# ============================================================================
# CONFIGURATION PAR PAGE
# ============================================================================

PAGE_CONFIG = {
    'overview': {
        'icon': '📊',
        'title': 'Vue d\'ensemble',
        'cache_ttl': 600,  # 10 min
    },
    'explorer': {
        'icon': '🔍',
        'title': 'Explorateur',
        'cache_ttl': 300,  # 5 min
    },
    'comparisons': {
        'icon': '🔄',
        'title': 'Comparaisons',
        'cache_ttl': 300,  # 5 min
    },
    'exports': {
        'icon': '💾',
        'title': 'Exports',
        'cache_ttl': 60,   # 1 min
    },
}


def get_page_config(page: str) -> dict:
    """Récupère la config d'une page."""
    return PAGE_CONFIG.get(page, {})
