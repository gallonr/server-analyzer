"""
Validation du fichier de configuration.
"""
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigError(Exception):
    """Exception levée pour erreur de configuration."""
    pass

def validate_config(config: Dict[str, Any]) -> None:
    """
    Valide la configuration.
    
    Args:
        config: Dictionnaire de configuration
        
    Raises:
        ConfigError: Si la configuration est invalide
    """
    # Vérifier présence clés obligatoires
    required_keys = ['root_paths', 'performance', 'database']
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Clé obligatoire manquante: {key}")
    
    # Vérifier root_paths non vide
    if not config['root_paths']:
        raise ConfigError("Au moins un chemin racine doit être spécifié")
    
    # Vérifier chemins existent
    for path in config['root_paths']:
        if not Path(path).exists():
            print(f"⚠️  Avertissement: Chemin n'existe pas: {path}")
    
    # Vérifier num_workers > 0
    num_workers = config['performance'].get('num_workers', 1)
    if num_workers < 1:
        raise ConfigError(f"num_workers doit être > 0, reçu: {num_workers}")
    
    print("✓ Configuration validée")

def load_and_validate_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Charge et valide le fichier de configuration.
    
    Args:
        config_path: Chemin vers config.yaml
        
    Returns:
        Dictionnaire de configuration validé
        
    Raises:
        ConfigError: Si configuration invalide
    """
    if not Path(config_path).exists():
        raise ConfigError(f"Fichier de configuration introuvable: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    validate_config(config)
    return config

if __name__ == "__main__":
    # Test
    try:
        config = load_and_validate_config()
        print("Configuration OK")
    except ConfigError as e:
        print(f"❌ Erreur: {e}")
