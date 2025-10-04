"""
Tests unitaires pour le module scanner.
"""

import pytest
import os
import time
from pathlib import Path
from src.scanner import FileScanner, ParallelScanner
from src.database import DatabaseManager


class TestFileScanner:
    """Tests pour FileScanner."""
    
    def test_extract_metadata_file(self, tmp_path):
        """Test extraction métadonnées d'un fichier."""
        # Créer un fichier de test
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")
        
        scanner = FileScanner(scan_id="test-scan")
        metadata = scanner.extract_metadata(str(test_file))
        
        assert metadata is not None
        assert metadata['scan_id'] == "test-scan"
        assert metadata['filename'] == "test.txt"
        assert metadata['extension'] == "txt"
        assert metadata['is_directory'] == 0
        assert metadata['size_bytes'] == 11  # "Hello World"
        assert metadata['error_message'] is None
    
    def test_extract_metadata_directory(self, tmp_path):
        """Test extraction métadonnées d'un dossier."""
        # Créer un dossier de test
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        scanner = FileScanner(scan_id="test-scan")
        metadata = scanner.extract_metadata(str(test_dir))
        
        assert metadata is not None
        assert metadata['filename'] == "testdir"
        assert metadata['is_directory'] == 1
        assert metadata['extension'] is None
        assert metadata['error_message'] is None
    
    def test_extract_metadata_permissions(self, tmp_path):
        """Test extraction permissions."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        test_file.chmod(0o644)
        
        scanner = FileScanner(scan_id="test-scan")
        metadata = scanner.extract_metadata(str(test_file))
        
        assert metadata is not None
        assert metadata['permissions'] is not None
        assert 'rw-' in metadata['permissions']
    
    def test_extract_metadata_timestamps(self, tmp_path):
        """Test extraction timestamps."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        scanner = FileScanner(scan_id="test-scan")
        metadata = scanner.extract_metadata(str(test_file))
        
        assert metadata is not None
        assert metadata['mtime'] is not None
        assert metadata['ctime'] is not None
        assert metadata['atime'] is not None
        assert metadata['scan_timestamp'] is not None
    
    def test_extract_metadata_nonexistent(self, tmp_path):
        """Test fichier inexistant."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        scanner = FileScanner(scan_id="test-scan")
        metadata = scanner.extract_metadata(str(nonexistent))
        
        assert metadata is not None
        assert metadata['error_message'] is not None
        assert "introuvable" in metadata['error_message'].lower()
    
    def test_should_exclude_directory(self, tmp_path):
        """Test exclusion de répertoire."""
        exclusions = {
            'directories': ['*/tmp/*', '*/cache/*'],
            'extensions': []
        }
        
        scanner = FileScanner(scan_id="test-scan", exclusions=exclusions)
        
        assert scanner.should_exclude('/data/tmp/file') == True
        assert scanner.should_exclude('/var/cache/data') == True
        assert scanner.should_exclude('/data/regular/file') == False
    
    def test_should_exclude_extension(self, tmp_path):
        """Test exclusion par extension."""
        exclusions = {
            'directories': [],
            'extensions': ['log', 'tmp', 'cache']
        }
        
        scanner = FileScanner(scan_id="test-scan", exclusions=exclusions)
        
        assert scanner.should_exclude('/data/file.log') == True
        assert scanner.should_exclude('/data/file.tmp') == True
        assert scanner.should_exclude('/data/file.txt') == False


class TestParallelScanner:
    """Tests pour ParallelScanner."""
    
    def test_discover_directories(self, tmp_path):
        """Test découverte de répertoires."""
        # Créer une arborescence de test
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir1" / "subdir1").mkdir()
        (tmp_path / "dir2" / "subdir2").mkdir()
        
        scanner = ParallelScanner(
            scan_id="test-scan",
            num_workers=2
        )
        
        directories = scanner.discover_directories([str(tmp_path)])
        
        # Doit inclure le répertoire racine et les sous-répertoires
        assert len(directories) >= 5
        assert str(tmp_path) in directories
        assert str(tmp_path / "dir1") in directories
        assert str(tmp_path / "dir2") in directories
    
    def test_discover_directories_with_exclusions(self, tmp_path):
        """Test découverte avec exclusions."""
        # Créer arborescence
        (tmp_path / "include").mkdir()
        (tmp_path / "exclude").mkdir()
        (tmp_path / "include" / "sub1").mkdir()
        (tmp_path / "exclude" / "sub2").mkdir()
        
        exclusions = {
            'directories': ['*/exclude/*'],
            'extensions': []
        }
        
        scanner = ParallelScanner(
            scan_id="test-scan",
            num_workers=2,
            exclusions=exclusions
        )
        
        directories = scanner.discover_directories([str(tmp_path)])
        
        # Ne doit pas inclure les dossiers exclus
        assert str(tmp_path / "include") in directories
        # Note: os.walk filtre les dirnames, donc exclude/sub2 ne sera pas découvert
    
    def test_scan_small_directory(self, tmp_path):
        """Test scan d'un petit répertoire."""
        # Créer quelques fichiers
        (tmp_path / "file1.txt").write_text("test1")
        (tmp_path / "file2.txt").write_text("test2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("test3")
        
        # Initialiser base de données
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=[str(tmp_path)],
            num_workers=2
        )
        
        # Lancer scan
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=2
        )
        
        stats = scanner.scan(
            root_paths=[str(tmp_path)],
            db_manager=db,
            checkpoint_interval=9999  # Pas de checkpoint pendant le test
        )
        
        # Vérifier résultats
        assert stats['files_scanned'] > 0
        assert stats['directories_scanned'] > 0
        
        # Vérifier que les fichiers sont en base
        total_files = db.get_total_files_count(scan_id)
        assert total_files >= 3  # Au moins les 3 fichiers créés
        
        db.close()
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scan d'un répertoire vide."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=[str(empty_dir)],
            num_workers=1
        )
        
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=1
        )
        
        stats = scanner.scan(
            root_paths=[str(empty_dir)],
            db_manager=db
        )
        
        # Le dossier lui-même est scanné
        assert stats['directories_scanned'] >= 1
        
        db.close()
    
    def test_scan_nonexistent_path(self, tmp_path):
        """Test scan d'un chemin inexistant."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=["/nonexistent/path"],
            num_workers=1
        )
        
        scanner = ParallelScanner(
            scan_id=scan_id,
            num_workers=1
        )
        
        stats = scanner.scan(
            root_paths=["/nonexistent/path"],
            db_manager=db
        )
        
        # Doit retourner 0 fichiers
        assert stats['files_scanned'] == 0
        
        db.close()
