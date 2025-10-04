"""
Tests unitaires pour le module stats.
"""

import pytest
import time
import json
from src.stats import (
    compute_directory_stats,
    compute_extension_stats,
    get_top_extensions,
    compute_owner_stats,
    get_top_owners,
    compute_temporal_distribution,
    get_oldest_newest_files,
    detect_large_files,
    detect_old_files,
    detect_duplicate_candidates,
    benchmark_query
)
from src.database import DatabaseManager


@pytest.fixture
def db_with_data(tmp_path):
    """Fixture avec base de données remplie."""
    db_path = tmp_path / "test_stats.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    db.init_schema()
    
    # Insérer données test
    scan_id = "test_scan_stats"
    cursor = db.conn.cursor()
    
    current_time = int(time.time())
    old_time = current_time - (365 * 86400)  # 1 an
    very_old_time = current_time - (800 * 86400)  # > 2 ans
    
    files = [
        # Dossier /data
        ('/data/file1.txt', '/data', 'file1.txt', 'txt', 1024, current_time, 'alice', 'alice', 1001, 1001, 0),
        ('/data/file2.pdf', '/data', 'file2.pdf', 'pdf', 2048, current_time, 'bob', 'bob', 1002, 1002, 0),
        ('/data/large.iso', '/data', 'large.iso', 'iso', 15*1024*1024*1024, old_time, 'alice', 'alice', 1001, 1001, 0),
        
        # Dossier /data/sub
        ('/data/sub/file3.txt', '/data/sub', 'file3.txt', 'txt', 512, current_time, 'alice', 'alice', 1001, 1001, 0),
        ('/data/sub/file4.csv', '/data/sub', 'file4.csv', 'csv', 1536, old_time, 'charlie', 'charlie', 1003, 1003, 0),
        
        # Dossier /backup (fichiers anciens)
        ('/backup/old1.bak', '/backup', 'old1.bak', 'bak', 4096, very_old_time, 'bob', 'bob', 1002, 1002, 0),
        ('/backup/old2.bak', '/backup', 'old2.bak', 'bak', 2048, very_old_time, 'bob', 'bob', 1002, 1002, 0),
        
        # Doublons potentiels
        ('/data/duplicate.txt', '/data', 'duplicate.txt', 'txt', 100, current_time, 'alice', 'alice', 1001, 1001, 0),
        ('/backup/duplicate.txt', '/backup', 'duplicate.txt', 'txt', 100, current_time, 'bob', 'bob', 1002, 1002, 0),
        
        # Répertoires
        ('/data', '/', 'data', None, 4096, current_time, 'root', 'root', 0, 0, 1),
        ('/data/sub', '/data', 'sub', None, 4096, current_time, 'root', 'root', 0, 0, 1),
    ]
    
    for file_data in files:
        cursor.execute("""
            INSERT INTO files (
                path, parent_dir, filename, extension, size_bytes, mtime,
                owner_name, group_name, owner_uid, owner_gid, is_directory,
                scan_timestamp, scan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, file_data + (current_time, scan_id))
    
    db.conn.commit()
    yield db, scan_id
    
    db.close()


def test_compute_directory_stats(db_with_data):
    """Test calcul stats dossiers."""
    db, scan_id = db_with_data
    
    count = compute_directory_stats(scan_id, db.conn)
    
    # Au moins 3 dossiers : /, /data, /data/sub, /backup
    assert count >= 3
    
        # Vérifier stats /data
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT total_files, total_size_bytes, extension_stats, owner_stats
        FROM directory_stats
        WHERE dir_path = '/data' AND scan_id = ?
    """, (scan_id,))
    
    row = cursor.fetchone()
    assert row is not None
    
    total_files = row[0]
    total_size = row[1]
    extension_stats = json.loads(row[2])
    owner_stats = json.loads(row[3])
    
    # 4 fichiers dans /data (txt, pdf, iso, duplicate.txt)
    assert total_files == 4
    
    # Vérifier répartition extensions (dans extension_stats)
    assert 'txt' in extension_stats or len(extension_stats) >= 1
    
    # Vérifier propriétaires
    assert 'alice' in owner_stats
    assert 'bob' in owner_stats


def test_compute_extension_stats(db_with_data):
    """Test stats extensions."""
    db, scan_id = db_with_data
    
    stats = compute_extension_stats(scan_id, db.conn)
    
    assert 'txt' in stats
    assert 'pdf' in stats
    assert 'bak' in stats
    assert 'csv' in stats
    assert 'iso' in stats
    
    # Vérifier stats txt (4 fichiers: file1.txt, file3.txt, et 2x duplicate.txt)
    txt_stats = stats['txt']
    assert txt_stats['count'] == 4
    assert txt_stats['total_size'] == 1024 + 512 + 100 + 100
    assert txt_stats['avg_size'] > 0
    assert txt_stats['min_size'] == 100
    assert txt_stats['max_size'] == 1024


def test_get_top_extensions(db_with_data):
    """Test top extensions."""
    db, scan_id = db_with_data
    
    # Top par taille
    top_size = get_top_extensions(scan_id, db.conn, limit=5, by='size')
    
    assert len(top_size) <= 5
    # iso devrait être en premier (15 GB)
    assert top_size[0][0] == 'iso'
    
    # Vérifier tri décroissant
    if len(top_size) > 1:
        assert top_size[0][2] >= top_size[1][2]
    
    # Top par count
    top_count = get_top_extensions(scan_id, db.conn, limit=5, by='count')
    
    assert len(top_count) <= 5
    # txt devrait être en premier (4 fichiers)
    assert top_count[0][0] == 'txt'
    assert top_count[0][1] == 4


def test_compute_owner_stats(db_with_data):
    """Test stats propriétaires."""
    db, scan_id = db_with_data
    
    stats = compute_owner_stats(scan_id, db.conn)
    
    assert 'alice' in stats
    assert 'bob' in stats
    assert 'charlie' in stats
    
    # alice : 4 fichiers (file1.txt, large.iso, file3.txt, duplicate.txt)
    assert stats['alice']['count'] == 4
    
    # bob : 4 fichiers (file2.pdf, old1.bak, old2.bak, duplicate.txt)
    assert stats['bob']['count'] == 4
    
    # charlie : 1 fichier
    assert stats['charlie']['count'] == 1


def test_get_top_owners(db_with_data):
    """Test top propriétaires."""
    db, scan_id = db_with_data
    
    top = get_top_owners(scan_id, db.conn, limit=3)
    
    assert len(top) <= 3
    
    # alice devrait être en premier (à cause de large.iso)
    assert top[0][0] == 'alice'
    
    # Vérifier tri décroissant par taille
    if len(top) > 1:
        assert top[0][2] >= top[1][2]


def test_compute_temporal_distribution_month(db_with_data):
    """Test distribution temporelle par mois."""
    db, scan_id = db_with_data
    
    distribution = compute_temporal_distribution(scan_id, db.conn, groupby='month')
    
    assert len(distribution) >= 1
    
    # Vérifier format clés
    for period in distribution.keys():
        assert '-' in period  # Format YYYY-MM
        assert len(period) == 7


def test_compute_temporal_distribution_year(db_with_data):
    """Test distribution temporelle par année."""
    db, scan_id = db_with_data
    
    distribution = compute_temporal_distribution(scan_id, db.conn, groupby='year')
    
    assert len(distribution) >= 1
    
    # Vérifier format clés
    for period in distribution.keys():
        assert len(period) == 4  # Format YYYY


def test_compute_temporal_distribution_invalid(db_with_data):
    """Test distribution temporelle avec groupby invalide."""
    db, scan_id = db_with_data
    
    with pytest.raises(ValueError):
        compute_temporal_distribution(scan_id, db.conn, groupby='invalid')


def test_get_oldest_newest_files(db_with_data):
    """Test fichiers les plus anciens/récents."""
    db, scan_id = db_with_data
    
    result = get_oldest_newest_files(scan_id, db.conn, limit=5)
    
    assert 'oldest' in result
    assert 'newest' in result
    
    oldest = result['oldest']
    newest = result['newest']
    
    assert len(oldest) >= 1
    assert len(newest) >= 1
    
    # Vérifier tri
    if len(oldest) > 1:
        assert oldest[0]['mtime'] <= oldest[1]['mtime']
    
    if len(newest) > 1:
        assert newest[0]['mtime'] >= newest[1]['mtime']


def test_detect_large_files(db_with_data):
    """Test détection gros fichiers."""
    db, scan_id = db_with_data
    
    # Seuil 10 GB
    threshold = 10 * 1024 * 1024 * 1024
    large = detect_large_files(scan_id, db.conn, threshold)
    
    # Doit trouver large.iso (15 GB)
    assert len(large) == 1
    assert large[0]['size_bytes'] == 15 * 1024 * 1024 * 1024
    assert 'large.iso' in large[0]['path']
    
    # Seuil 1 KB
    threshold = 1024
    large = detect_large_files(scan_id, db.conn, threshold)
    
    # Devrait trouver plusieurs fichiers
    assert len(large) >= 3


def test_detect_old_files(db_with_data):
    """Test détection fichiers anciens."""
    db, scan_id = db_with_data
    
    # Fichiers > 2 ans
    old = detect_old_files(scan_id, db.conn, days_threshold=730)
    
    # Doit trouver old1.bak et old2.bak (> 800 jours)
    assert len(old) == 2
    assert all('.bak' in f['path'] for f in old)
    
    # Fichiers > 1 jour (devrait trouver ceux > 1 an et > 2 ans)
    old = detect_old_files(scan_id, db.conn, days_threshold=1)
    
    # large.iso (1 an), file4.csv (1 an), old1.bak, old2.bak
    assert len(old) >= 4


def test_detect_duplicate_candidates(db_with_data):
    """Test détection doublons."""
    db, scan_id = db_with_data
    
    duplicates = detect_duplicate_candidates(scan_id, db.conn)
    
    # Doit trouver duplicate.txt (même nom, même taille)
    assert len(duplicates) == 1
    
    dup = duplicates[0]
    assert dup['name'] == 'duplicate.txt'
    assert dup['size_bytes'] == 100
    assert dup['count'] == 2
    assert len(dup['paths']) == 2
    assert '/data/duplicate.txt' in dup['paths']
    assert '/backup/duplicate.txt' in dup['paths']


def test_benchmark_query(db_with_data):
    """Test fonction benchmark."""
    db, scan_id = db_with_data
    
    def dummy_query():
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files WHERE scan_id = ?", (scan_id,))
        cursor.fetchone()
    
    avg_time = benchmark_query(dummy_query, iterations=3)
    
    assert avg_time >= 0
    assert avg_time < 1.0  # Devrait être très rapide


def test_compute_directory_stats_empty(tmp_path):
    """Test stats avec base vide."""
    db_path = tmp_path / "empty.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    db.init_schema()
    
    count = compute_directory_stats("empty_scan", db.conn)
    
    assert count == 0
    
    db.close()


def test_compute_extension_stats_empty(tmp_path):
    """Test stats extensions avec base vide."""
    db_path = tmp_path / "empty.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    db.init_schema()
    
    stats = compute_extension_stats("empty_scan", db.conn)
    
    assert stats == {}
    
    db.close()


def test_detect_large_files_none(db_with_data):
    """Test détection gros fichiers avec seuil très élevé."""
    db, scan_id = db_with_data
    
    # Seuil 100 TB
    threshold = 100 * 1024 * 1024 * 1024 * 1024
    large = detect_large_files(scan_id, db.conn, threshold)
    
    assert len(large) == 0


def test_detect_old_files_none(db_with_data):
    """Test détection fichiers anciens avec seuil très élevé."""
    db, scan_id = db_with_data
    
    # Fichiers > 10 ans
    old = detect_old_files(scan_id, db.conn, days_threshold=3650)
    
    assert len(old) == 0


def test_directory_stats_json_serialization(db_with_data):
    """Test que les JSON sont bien sérialisés."""
    db, scan_id = db_with_data
    
    compute_directory_stats(scan_id, db.conn)
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT extension_stats, owner_stats
        FROM directory_stats
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    
    # Vérifier que ce sont bien des chaînes JSON valides
    extension_stats = json.loads(row[0])
    owner_stats = json.loads(row[1])
    
    assert isinstance(extension_stats, dict)
    assert isinstance(owner_stats, dict)
