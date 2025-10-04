"""
Module utilitaire pour le scanner de serveur.

Contient les fonctions de logging, configuration et helpers.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import yaml
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ConfigError(Exception):
    """Exception levée lors d'une configuration invalide."""
    pass


def setup_logging(config: dict) -> logging.Logger:
    """
    Configure le système de logging avec rotation automatique.
    
    Args:
        config: Configuration (dict avec clé 'logging')
        
    Returns:
        Logger configuré
        
    Examples:
        >>> config = {'logging': {'level': 'INFO', 'file': 'logs/scan.log'}}
        >>> logger = setup_logging(config)
    """
    log_config = config.get('logging', {})
    
    # Niveau de log
    level = getattr(logging, log_config.get('level', 'INFO'))
    
    # Format
    log_format = log_config.get('format', 
                                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)
    
    # Fichier log avec timestamp
    log_file = log_config.get('file', 'logs/scan_{timestamp}.log')
    log_file = log_file.format(timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    # Créer dossier logs si nécessaire
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Handler fichier avec rotation
    rotation = log_config.get('rotation', {})
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=rotation.get('max_bytes', 100*1024*1024),  # 100 MB par défaut
        backupCount=rotation.get('backup_count', 10)
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Logger racine
    logger = logging.getLogger('server_analyzer')
    logger.setLevel(level)
    
    # Supprimer les handlers existants pour éviter les doublons
    logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging configuré - Niveau: {log_config.get('level', 'INFO')}")
    logger.info(f"Fichier log: {log_file}")
    
    return logger


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """
    Charge et valide le fichier de configuration YAML.
    
    Args:
        path: Chemin vers config.yaml
        
    Returns:
        Configuration validée
        
    Raises:
        ConfigError: Si configuration invalide ou fichier manquant
        
    Examples:
        >>> config = load_config('config.yaml')
        >>> print(config['performance']['num_workers'])
    """
    config_path = Path(path)
    
    if not config_path.exists():
        raise ConfigError(f"Fichier de configuration introuvable: {path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Erreur parsing YAML: {e}")
    
    # Validation
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Valide la structure et le contenu de la configuration.
    
    Args:
        config: Configuration à valider
        
    Raises:
        ConfigError: Si configuration invalide
    """
    # Clés obligatoires
    required = ['root_paths', 'performance', 'database']
    for key in required:
        if key not in config:
            raise ConfigError(f"Clé obligatoire manquante: {key}")
    
    # root_paths non vide
    if not config['root_paths']:
        raise ConfigError("Au moins un chemin racine requis")
    
    # num_workers > 0
    num_workers = config['performance'].get('num_workers', 0)
    if num_workers < 1:
        raise ConfigError(f"num_workers doit être > 0, reçu: {num_workers}")
    
    # Vérifier chemins existent (warning seulement)
    logger = logging.getLogger('server_analyzer')
    for path in config['root_paths']:
        if not Path(path).exists():
            logger.warning(f"Chemin n'existe pas: {path}")


def format_size(bytes: int) -> str:
    """
    Formate une taille en octets en format lisible.
    
    Args:
        bytes: Taille en octets
        
    Returns:
        Taille formatée (ex: "1.5 GB")
        
    Examples:
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1536)
        '1.5 KB'
        >>> format_size(1073741824)
        '1.0 GB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} EB"


def format_timestamp(epoch: int) -> str:
    """
    Formate un timestamp epoch en datetime lisible.
    
    Args:
        epoch: Timestamp Unix (secondes depuis 1970)
        
    Returns:
        Date/heure formatée (YYYY-MM-DD HH:MM:SS)
        
    Examples:
        >>> format_timestamp(1609459200)
        '2021-01-01 00:00:00'
    """
    return datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')


def get_extension(filename: str) -> str:
    """
    Extrait l'extension d'un nom de fichier.
    
    Args:
        filename: Nom de fichier
        
    Returns:
        Extension en minuscules sans le point, ou chaîne vide
        
    Examples:
        >>> get_extension('file.txt')
        'txt'
        >>> get_extension('archive.tar.gz')
        'gz'
        >>> get_extension('no_extension')
        ''
    """
    _, ext = os.path.splitext(filename)
    return ext[1:].lower() if ext else ''


def is_excluded(path: str, exclusions: dict) -> bool:
    """
    Vérifie si un chemin doit être exclu selon la configuration.
    
    Args:
        path: Chemin à vérifier
        exclusions: Dict avec 'directories' et 'extensions'
        
    Returns:
        True si doit être exclu, False sinon
        
    Examples:
        >>> exclusions = {'directories': ['*/tmp/*'], 'extensions': ['tmp']}
        >>> is_excluded('/data/tmp/file', exclusions)
        True
        >>> is_excluded('/data/file.tmp', exclusions)
        True
    """
    # Vérifier dossiers exclus
    for pattern in exclusions.get('directories', []):
        if fnmatch.fnmatch(path, pattern):
            return True
    
    # Vérifier extensions exclues
    ext = get_extension(path)
    if ext in exclusions.get('extensions', []):
        return True
    
    return False
