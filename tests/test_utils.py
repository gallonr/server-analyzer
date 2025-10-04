"""
Tests unitaires pour le module utils.
"""

import pytest
import logging
import os
from pathlib import Path
from src.utils import (
    setup_logging, load_config, ConfigError,
    format_size, format_timestamp, get_extension, is_excluded
)


class TestLogging:
    """Tests pour la fonction setup_logging."""
    
    def test_setup_logging_default(self, tmp_path):
        """Test configuration logging par défaut."""
        log_file = tmp_path / "test.log"
        config = {
            'logging': {
                'level': 'INFO',
                'file': str(log_file)
            }
        }
        
        logger = setup_logging(config)
        
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO
        assert log_file.exists()
    
    def test_setup_logging_debug_level(self, tmp_path):
        """Test avec niveau DEBUG."""
        config = {
            'logging': {
                'level': 'DEBUG',
                'file': str(tmp_path / "debug.log")
            }
        }
        
        logger = setup_logging(config)
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_creates_directory(self, tmp_path):
        """Test que le répertoire logs est créé."""
        log_file = tmp_path / "subdir" / "test.log"
        config = {
            'logging': {
                'file': str(log_file)
            }
        }
        
        logger = setup_logging(config)
        assert log_file.parent.exists()
        assert log_file.exists()


class TestConfiguration:
    """Tests pour load_config et validation."""
    
    def test_load_config_valid(self, tmp_path):
        """Test chargement configuration valide."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
root_paths:
  - /tmp
performance:
  num_workers: 4
  batch_size: 1000
database:
  path: test.db
""")
        
        config = load_config(str(config_file))
        assert config['performance']['num_workers'] == 4
        assert config['database']['path'] == 'test.db'
    
    def test_load_config_file_not_found(self):
        """Test fichier config introuvable."""
        with pytest.raises(ConfigError, match="introuvable"):
            load_config("nonexistent.yaml")
    
    def test_load_config_missing_root_paths(self, tmp_path):
        """Test config sans root_paths."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
performance:
  num_workers: 4
database:
  path: test.db
""")
        
        with pytest.raises(ConfigError, match="root_paths"):
            load_config(str(config_file))
    
    def test_load_config_missing_performance(self, tmp_path):
        """Test config sans performance."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
root_paths:
  - /tmp
database:
  path: test.db
""")
        
        with pytest.raises(ConfigError, match="performance"):
            load_config(str(config_file))
    
    def test_load_config_empty_root_paths(self, tmp_path):
        """Test avec root_paths vide."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
root_paths: []
performance:
  num_workers: 4
database:
  path: test.db
""")
        
        with pytest.raises(ConfigError, match="Au moins un chemin"):
            load_config(str(config_file))
    
    def test_load_config_invalid_num_workers(self, tmp_path):
        """Test avec num_workers invalide."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
root_paths:
  - /tmp
performance:
  num_workers: 0
database:
  path: test.db
""")
        
        with pytest.raises(ConfigError, match="num_workers"):
            load_config(str(config_file))


class TestFormatSize:
    """Tests pour format_size."""
    
    def test_format_bytes(self):
        """Test formatage octets."""
        assert format_size(0) == "0.0 B"
        assert format_size(512) == "512.0 B"
    
    def test_format_kilobytes(self):
        """Test formatage kilo-octets."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
    
    def test_format_megabytes(self):
        """Test formatage méga-octets."""
        assert format_size(1048576) == "1.0 MB"
        assert format_size(1572864) == "1.5 MB"
    
    def test_format_gigabytes(self):
        """Test formatage giga-octets."""
        assert format_size(1073741824) == "1.0 GB"
        assert format_size(1610612736) == "1.5 GB"
    
    def test_format_terabytes(self):
        """Test formatage téra-octets."""
        assert format_size(1099511627776) == "1.0 TB"


class TestFormatTimestamp:
    """Tests pour format_timestamp."""
    
    def test_format_timestamp_epoch_zero(self):
        """Test avec epoch = 0."""
        # 1970-01-01 00:00:00 UTC (peut varier selon timezone)
        result = format_timestamp(0)
        assert "1970" in result
    
    def test_format_timestamp_specific_date(self):
        """Test avec date spécifique."""
        # 2021-01-01 00:00:00 UTC
        timestamp = 1609459200
        result = format_timestamp(timestamp)
        assert "2021-01-01" in result


class TestGetExtension:
    """Tests pour get_extension."""
    
    def test_get_extension_simple(self):
        """Test extension simple."""
        assert get_extension("file.txt") == "txt"
        assert get_extension("document.pdf") == "pdf"
    
    def test_get_extension_uppercase(self):
        """Test conversion en minuscules."""
        assert get_extension("FILE.TXT") == "txt"
        assert get_extension("Document.PDF") == "pdf"
    
    def test_get_extension_multiple_dots(self):
        """Test fichier avec plusieurs points."""
        assert get_extension("archive.tar.gz") == "gz"
        assert get_extension("backup.2024.zip") == "zip"
    
    def test_get_extension_no_extension(self):
        """Test fichier sans extension."""
        assert get_extension("README") == ""
        assert get_extension("Makefile") == ""
    
    def test_get_extension_hidden_file(self):
        """Test fichier caché."""
        # os.path.splitext considère les fichiers cachés sans extension
        assert get_extension(".gitignore") == ""
        assert get_extension(".bashrc") == ""
        # Mais les fichiers cachés avec extension fonctionnent
        assert get_extension(".hidden.txt") == "txt"


class TestIsExcluded:
    """Tests pour is_excluded."""
    
    def test_is_excluded_directory_pattern(self):
        """Test exclusion par pattern de répertoire."""
        exclusions = {
            'directories': ['/tmp/*', '*/cache/*'],
            'extensions': []
        }
        
        assert is_excluded('/tmp/file', exclusions) == True
        assert is_excluded('/data/cache/file', exclusions) == True
        assert is_excluded('/data/file', exclusions) == False
    
    def test_is_excluded_extension(self):
        """Test exclusion par extension."""
        exclusions = {
            'directories': [],
            'extensions': ['tmp', 'cache', 'log']
        }
        
        assert is_excluded('/data/file.tmp', exclusions) == True
        assert is_excluded('/data/file.cache', exclusions) == True
        assert is_excluded('/data/file.txt', exclusions) == False
    
    def test_is_excluded_combined(self):
        """Test exclusion combinée."""
        exclusions = {
            'directories': ['*/backup/*'],
            'extensions': ['bak']
        }
        
        assert is_excluded('/data/backup/file', exclusions) == True
        assert is_excluded('/data/file.bak', exclusions) == True
        assert is_excluded('/data/file.txt', exclusions) == False
    
    def test_is_excluded_empty_exclusions(self):
        """Test sans exclusions."""
        exclusions = {
            'directories': [],
            'extensions': []
        }
        
        assert is_excluded('/any/path', exclusions) == False
        assert is_excluded('/any/file.any', exclusions) == False
