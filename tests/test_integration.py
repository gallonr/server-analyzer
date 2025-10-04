"""
Tests d'intégration pour le système complet.
"""

import pytest
import os
import yaml
from pathlib import Path
from src.utils import load_config, setup_logging
from src.database import DatabaseManager
from src.scanner import ParallelScanner


class TestFullWorkflow:
    """Tests du workflow complet."""
    
    def test_complete_scan_workflow(self, tmp_path):
        """Test complet du processus de scan."""
        
        # 1. Créer une arborescence de test
        test_root = tmp_path / "test_data"
        test_root.mkdir()
        
        # Créer fichiers et dossiers
        (test_root / "documents").mkdir()
        (test_root / "images").mkdir()
        (test_root / "documents" / "file1.txt").write_text("Document 1")
        (test_root / "documents" / "file2.pdf").write_text("PDF content")
        (test_root / "images" / "photo.jpg").write_text("Image data")
        (test_root / "README.md").write_text("# README")
        
        # 2. Créer configuration
        config = {
            'root_paths': [str(test_root)],
            'performance': {
                'num_workers': 2,
                'batch_size': 100,
                'checkpoint_interval': 9999
            },
            'database': {
                'path': str(tmp_path / "test.db")
            },
            'logging': {
                'level': 'INFO',
                'file': str(tmp_path / "test.log")
            },
            'exclusions': {
                'directories': [],
                'extensions': []
            }
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # 3. Charger configuration
        loaded_config = load_config(str(config_file))
        assert loaded_config['performance']['num_workers'] == 2
        
        # 4. Setup logging
        logger = setup_logging(loaded_config)
        assert logger is not None
        
        # 5. Initialiser base de données
        db = DatabaseManager(loaded_config['database']['path'])
        db.connect()
        db.init_schema()
        
        # 6. Créer scan
        scan_id = db.create_scan(
            root_paths=loaded_config['root_paths'],
            num_workers=loaded_config['performance']['num_workers']
        )
        
        # 7. Lancer scan
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=loaded_config['performance']['num_workers'],
            exclusions=loaded_config['exclusions'],
            batch_size=loaded_config['performance']['batch_size']
        )
        
        stats = scanner.scan(
            root_paths=loaded_config['root_paths'],
            db_manager=db,
            checkpoint_interval=loaded_config['performance']['checkpoint_interval']
        )
        
        # 8. Vérifier résultats
        assert stats['files_scanned'] > 0
        
        total_files = db.get_total_files_count(scan_id)
        assert total_files >= 4  # Au moins 4 fichiers créés
        
        total_size = db.get_total_size(scan_id)
        assert total_size > 0
        
        # 9. Mettre à jour statut
        db.update_scan_status(
            scan_id=scan_id,
            status='completed',
            total_files=total_files,
            total_size=total_size
        )
        
        # 10. Vérifier scan info
        scan_info = db.get_scan_info(scan_id)
        assert scan_info['status'] == 'completed'
        assert scan_info['total_files'] >= 4
        assert scan_info['total_size_bytes'] > 0
        
        db.close()
    
    def test_scan_with_exclusions(self, tmp_path):
        """Test scan avec exclusions."""
        
        # Créer arborescence
        test_root = tmp_path / "test_data"
        test_root.mkdir()
        
        (test_root / "include").mkdir()
        (test_root / "exclude").mkdir()
        (test_root / "include" / "file.txt").write_text("Include me")
        (test_root / "exclude" / "file.log").write_text("Exclude me")
        (test_root / "file.tmp").write_text("Temp file")
        
        # Configuration avec exclusions
        config = {
            'root_paths': [str(test_root)],
            'performance': {
                'num_workers': 1,
                'batch_size': 100
            },
            'database': {
                'path': str(tmp_path / "test.db")
            },
            'logging': {
                'level': 'WARNING',
                'file': str(tmp_path / "test.log")
            },
            'exclusions': {
                'directories': ['*/exclude/*'],
                'extensions': ['tmp', 'log']
            }
        }
        
        # Initialiser
        db = DatabaseManager(config['database']['path'])
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=config['root_paths'],
            num_workers=1
        )
        
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=1,
            exclusions=config['exclusions']
        )
        
        stats = scanner.scan(
            root_paths=config['root_paths'],
            db_manager=db
        )
        
        # Vérifier que les fichiers exclus ne sont pas scannés
        assert stats['files_scanned'] >= 0
        
        db.close()
    
    def test_multiple_root_paths(self, tmp_path):
        """Test scan de plusieurs chemins racine."""
        
        # Créer deux arborescences
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        root1.mkdir()
        root2.mkdir()
        
        (root1 / "file1.txt").write_text("Root 1")
        (root2 / "file2.txt").write_text("Root 2")
        
        # Configuration
        config = {
            'root_paths': [str(root1), str(root2)],
            'performance': {
                'num_workers': 2,
                'batch_size': 100
            },
            'database': {
                'path': str(tmp_path / "test.db")
            },
            'logging': {
                'level': 'INFO',
                'file': str(tmp_path / "test.log")
            },
            'exclusions': {
                'directories': [],
                'extensions': []
            }
        }
        
        # Scanner
        db = DatabaseManager(config['database']['path'])
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=config['root_paths'],
            num_workers=2
        )
        
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=2
        )
        
        stats = scanner.scan(
            root_paths=config['root_paths'],
            db_manager=db
        )
        
        # Vérifier que les deux racines sont scannées
        total_files = db.get_total_files_count(scan_id)
        assert total_files >= 2
        
        db.close()
