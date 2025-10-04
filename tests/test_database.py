"""
Tests unitaires pour le module database.
"""

import pytest
import sqlite3
from pathlib import Path
from src.database import DatabaseManager


class TestDatabaseManager:
    """Tests pour DatabaseManager."""
    
    def test_database_init(self, tmp_path):
        """Test initialisation base de données."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        # Vérifier que les tables sont créées
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'files' in tables
        assert 'directory_stats' in tables
        assert 'scans' in tables
        
        db.close()
    
    def test_pragma_configuration(self, tmp_path):
        """Test configuration PRAGMA."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        
        cursor = db.conn.cursor()
        
        # Vérifier WAL mode
        cursor.execute("PRAGMA journal_mode;")
        assert cursor.fetchone()[0].lower() == 'wal'
        
        # Vérifier synchronous
        cursor.execute("PRAGMA synchronous;")
        result = cursor.fetchone()[0]
        assert result in [1, 'NORMAL']  # 1 = NORMAL
        
        db.close()
    
    def test_create_scan(self, tmp_path):
        """Test création d'un scan."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=['/tmp', '/data'],
            num_workers=4
        )
        
        assert scan_id is not None
        
        # Vérifier que le scan existe
        scan_info = db.get_scan_info(scan_id)
        assert scan_info is not None
        assert scan_info['status'] == 'running'
        assert scan_info['num_workers'] == 4
        
        db.close()
    
    def test_update_scan_status(self, tmp_path):
        """Test mise à jour statut scan."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(
            root_paths=['/tmp'],
            num_workers=2
        )
        
        # Mettre à jour
        db.update_scan_status(
            scan_id=scan_id,
            status='completed',
            total_files=1000,
            total_size=1073741824
        )
        
        scan_info = db.get_scan_info(scan_id)
        assert scan_info['status'] == 'completed'
        assert scan_info['total_files'] == 1000
        assert scan_info['total_size_bytes'] == 1073741824
        assert scan_info['end_time'] is not None
        
        db.close()
    
    def test_batch_insert_files(self, tmp_path):
        """Test insertion par lots."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(root_paths=['/tmp'], num_workers=1)
        
        # Créer données de test
        files_data = [
            {
                'scan_id': scan_id,
                'path': f'/tmp/file{i}.txt',
                'filename': f'file{i}.txt',
                'parent_dir': '/tmp',
                'size_bytes': 1024 * i,
                'is_directory': 0,
                'extension': 'txt',
                'owner_uid': 1000,
                'owner_gid': 1000,
                'owner_name': 'testuser',
                'group_name': 'testgroup',
                'permissions': '-rw-r--r--',
                'mtime': 1609459200,
                'ctime': 1609459200,
                'atime': 1609459200,
                'inode': 1000 + i,
                'num_links': 1,
                'scan_timestamp': 1609459200,
                'error_message': None
            }
            for i in range(100)
        ]
        
        db.batch_insert_files(files_data)
        
        # Vérifier insertion
        count = db.get_total_files_count(scan_id)
        assert count == 100
        
        db.close()
    
    def test_get_total_files_count(self, tmp_path):
        """Test comptage fichiers."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(root_paths=['/tmp'], num_workers=1)
        
        # Insérer fichiers et dossiers
        files_data = [
            {
                'scan_id': scan_id,
                'path': f'/tmp/file{i}',
                'filename': f'file{i}',
                'parent_dir': '/tmp',
                'size_bytes': 1024,
                'is_directory': 0,  # Fichier
                'scan_timestamp': 1609459200
            }
            for i in range(50)
        ] + [
            {
                'scan_id': scan_id,
                'path': f'/tmp/dir{i}',
                'filename': f'dir{i}',
                'parent_dir': '/tmp',
                'size_bytes': 0,
                'is_directory': 1,  # Dossier
                'scan_timestamp': 1609459200
            }
            for i in range(10)
        ]
        
        db.batch_insert_files(files_data)
        
        # Ne doit compter que les fichiers (is_directory=0)
        count = db.get_total_files_count(scan_id)
        assert count == 50
        
        db.close()
    
    def test_get_total_size(self, tmp_path):
        """Test calcul taille totale."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        scan_id = db.create_scan(root_paths=['/tmp'], num_workers=1)
        
        files_data = [
            {
                'scan_id': scan_id,
                'path': f'/tmp/file{i}',
                'filename': f'file{i}',
                'parent_dir': '/tmp',
                'size_bytes': 1024,
                'is_directory': 0,
                'scan_timestamp': 1609459200
            }
            for i in range(100)
        ]
        
        db.batch_insert_files(files_data)
        
        total_size = db.get_total_size(scan_id)
        assert total_size == 1024 * 100
        
        db.close()
    
    def test_get_latest_scan_id(self, tmp_path):
        """Test récupération dernier scan."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        # Créer plusieurs scans
        import time
        scan_id1 = db.create_scan(root_paths=['/tmp'], num_workers=1)
        time.sleep(0.1)
        scan_id2 = db.create_scan(root_paths=['/data'], num_workers=2)
        
        # Le dernier doit être scan_id2
        latest = db.get_latest_scan_id()
        assert latest == scan_id2
        
        db.close()
    
    def test_indexes_created(self, tmp_path):
        """Test que les index sont créés."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        db.init_schema()
        
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index'
            ORDER BY name
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Vérifier quelques index importants
        assert any('idx_files_scan_id' in idx for idx in indexes)
        assert any('idx_files_extension' in idx for idx in indexes)
        assert any('idx_files_size_bytes' in idx for idx in indexes)
        
        db.close()
