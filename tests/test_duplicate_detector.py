"""
Tests pour le module duplicate_detector.
"""

import pytest
import tempfile
import os
from pathlib import Path
import time

from duplicate_detector import DuplicateDetector, find_duplicates_quick, get_duplicate_report


@pytest.fixture
def db_with_duplicates(db_with_data):
    """
    Fixture avec base de données contenant des doublons.
    
    Returns:
        Tuple (DatabaseManager, scan_id, temp_dir)
    """
    db, scan_id = db_with_data
    
    # Créer des fichiers temporaires pour tester les hash
    temp_dir = tempfile.mkdtemp()
    
    # Créer des vrais doublons (même contenu)
    content1 = b"This is duplicate content for testing"
    
    file1 = Path(temp_dir) / "dup1.txt"
    file2 = Path(temp_dir) / "dup2.txt"
    file3 = Path(temp_dir) / "dup3.txt"
    
    file1.write_bytes(content1)
    file2.write_bytes(content1)
    file3.write_bytes(content1)
    
    # Ajouter à la base de données
    cursor = db.conn.cursor()
    
    files_to_add = [
        (scan_id, str(file1), "dup1.txt", str(temp_dir), len(content1), 0, "txt", 
         1000, 1000, "testuser", "testgroup", "-rw-r--r--", 
         int(time.time()), int(time.time()), int(time.time()), 
         100001, 1, int(time.time()), None),
        (scan_id, str(file2), "dup2.txt", str(temp_dir), len(content1), 0, "txt",
         1000, 1000, "testuser", "testgroup", "-rw-r--r--",
         int(time.time()), int(time.time()), int(time.time()),
         100002, 1, int(time.time()), None),
        (scan_id, str(file3), "dup3.txt", str(temp_dir), len(content1), 0, "txt",
         1000, 1000, "testuser", "testgroup", "-rw-r--r--",
         int(time.time()), int(time.time()), int(time.time()),
         100003, 1, int(time.time()), None)
    ]
    
    cursor.executemany("""
        INSERT INTO files (
            scan_id, path, filename, parent_dir, size_bytes, is_directory,
            extension, owner_uid, owner_gid, owner_name, group_name,
            permissions, mtime, ctime, atime, inode, num_links,
            scan_timestamp, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, files_to_add)
    
    db.conn.commit()
    
    yield db, scan_id, temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_duplicate_detector_init(db_with_data):
    """Test initialisation du détecteur."""
    db, scan_id = db_with_data
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    assert detector.db_conn is not None
    assert detector.scan_id == scan_id
    assert detector.CHUNK_SIZE == 1024 * 1024
    assert detector.PARTIAL_HASH_SIZE == 8192


def test_find_duplicates_by_size(db_with_data):
    """Test détection par taille."""
    db, scan_id = db_with_data
    
    detector = DuplicateDetector(db.conn, scan_id)
    groups = detector.find_duplicates_by_size(min_size=0)
    
    # La fixture a duplicate.txt (2 fois, 100 bytes chacun)
    assert len(groups) >= 1
    
    # Trouver le groupe duplicate.txt
    dup_group = next((g for g in groups if g['size_bytes'] == 100), None)
    assert dup_group is not None
    assert dup_group['count'] == 2
    assert '/data/duplicate.txt' in dup_group['paths']
    assert '/backup/duplicate.txt' in dup_group['paths']


def test_find_duplicates_by_size_min_threshold(db_with_data):
    """Test seuil minimum de taille."""
    db, scan_id = db_with_data
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    # Avec seuil élevé, ne doit pas trouver les petits fichiers
    groups = detector.find_duplicates_by_size(min_size=2000)
    
    # Ne doit pas inclure duplicate.txt (100 bytes)
    dup_group = next((g for g in groups if g['size_bytes'] == 100), None)
    assert dup_group is None


def test_calculate_file_hash(db_with_duplicates):
    """Test calcul de hash."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    file1 = Path(temp_dir) / "dup1.txt"
    file2 = Path(temp_dir) / "dup2.txt"
    
    # Hash complet
    hash1 = detector._calculate_file_hash(str(file1), partial=False)
    hash2 = detector._calculate_file_hash(str(file2), partial=False)
    
    assert hash1 is not None
    assert hash2 is not None
    assert hash1 == hash2  # Même contenu = même hash


def test_calculate_partial_hash(db_with_duplicates):
    """Test calcul de hash partiel."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    file1 = Path(temp_dir) / "dup1.txt"
    
    # Hash partiel vs complet
    hash_partial = detector._calculate_file_hash(str(file1), partial=True)
    hash_full = detector._calculate_file_hash(str(file1), partial=False)
    
    assert hash_partial is not None
    assert hash_full is not None
    # Pour petit fichier, hash partiel et complet peuvent être identiques
    # car le fichier est plus petit que PARTIAL_HASH_SIZE


def test_find_duplicates_by_partial_hash(db_with_duplicates):
    """Test détection par hash partiel."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    # D'abord grouper par taille
    size_groups = detector.find_duplicates_by_size(min_size=0)
    
    # Puis par hash partiel
    partial_groups = detector.find_duplicates_by_partial_hash(size_groups)
    
    assert len(partial_groups) >= 1
    
    # Vérifier qu'on a bien des groupes avec plusieurs fichiers
    for group in partial_groups:
        assert len(group['paths']) >= 2
        assert 'partial_hash' in group


def test_find_duplicates_by_full_hash(db_with_duplicates):
    """Test validation par hash complet."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    # Pipeline complet
    size_groups = detector.find_duplicates_by_size(min_size=0)
    partial_groups = detector.find_duplicates_by_partial_hash(size_groups)
    full_groups = detector.find_duplicates_by_full_hash(partial_groups)
    
    assert len(full_groups) >= 1
    
    # Vérifier structure des groupes
    for group in full_groups:
        assert 'hash' in group
        assert 'size_bytes' in group
        assert 'count' in group
        assert 'paths' in group
        assert group['count'] >= 2
        assert len(group['paths']) >= 2


def test_detect_all_duplicates(db_with_duplicates):
    """Test détection complète."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    report = detector.detect_all_duplicates(min_size=0)
    
    # Vérifier structure du rapport
    assert 'duplicate_groups' in report
    assert 'total_groups' in report
    assert 'total_duplicates' in report
    assert 'wasted_space' in report
    assert 'execution_time' in report
    
    # Doit avoir trouvé des doublons
    assert report['total_groups'] >= 1
    assert report['total_duplicates'] >= 2
    assert report['wasted_space'] > 0


def test_detect_all_duplicates_no_duplicates(tmp_db):
    """Test détection sans doublons."""
    db = tmp_db
    scan_id = "test_scan_no_dup"
    
    # Créer scan sans doublons
    db.create_scan(["/tmp"], 4)
    
    cursor = db.conn.cursor()
    cursor.execute("""
        UPDATE scans SET id = ? WHERE id != ?
    """, (scan_id, scan_id))
    db.conn.commit()
    
    detector = DuplicateDetector(db.conn, scan_id)
    report = detector.detect_all_duplicates(min_size=0)
    
    # Aucun doublon
    assert report['total_groups'] == 0
    assert report['total_duplicates'] == 0
    assert report['wasted_space'] == 0


def test_get_duplicate_details(db_with_duplicates):
    """Test enrichissement des détails."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    # Obtenir groupes
    report = detector.detect_all_duplicates(min_size=0)
    groups = report['duplicate_groups']
    
    # Enrichir
    enriched = detector.get_duplicate_details(groups)
    
    assert len(enriched) >= 1
    
    # Vérifier structure enrichie
    for group in enriched:
        assert 'hash' in group
        assert 'size_bytes' in group
        assert 'count' in group
        assert 'files' in group
        assert 'oldest_file' in group
        
        # Vérifier détails fichiers
        for file in group['files']:
            assert 'path' in file
            assert 'filename' in file
            assert 'owner' in file
            assert 'mtime' in file
            assert 'permissions' in file


def test_find_duplicates_quick(db_with_duplicates):
    """Test fonction helper rapide."""
    db, scan_id, temp_dir = db_with_duplicates
    
    report = find_duplicates_quick(scan_id, db.conn, min_size=0)
    
    assert 'duplicate_groups' in report
    assert 'total_groups' in report
    assert report['total_groups'] >= 1


def test_get_duplicate_report(db_with_duplicates):
    """Test rapport complet avec enrichissement."""
    db, scan_id, temp_dir = db_with_duplicates
    
    report = get_duplicate_report(scan_id, db.conn, min_size=0)
    
    assert 'duplicate_groups' in report
    
    # Groupes doivent être enrichis
    if report['duplicate_groups']:
        group = report['duplicate_groups'][0]
        assert 'files' in group
        assert len(group['files']) >= 2
        
        # Vérifier métadonnées complètes
        file = group['files'][0]
        assert 'path' in file
        assert 'filename' in file
        assert 'owner' in file


def test_wasted_space_calculation(db_with_duplicates):
    """Test calcul espace gaspillé."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    report = detector.detect_all_duplicates(min_size=0)
    
    # Calculer manuellement
    expected_wasted = 0
    for group in report['duplicate_groups']:
        redundant = group['count'] - 1
        expected_wasted += group['size_bytes'] * redundant
    
    assert report['wasted_space'] == expected_wasted


def test_hash_error_handling(tmp_db):
    """Test gestion erreurs de hash."""
    db = tmp_db
    scan_id = "test_scan_hash_error"
    
    db.create_scan(["/tmp"], 4)
    
    cursor = db.conn.cursor()
    cursor.execute("""
        UPDATE scans SET id = ? WHERE id != ?
    """, (scan_id, scan_id))
    
    # Ajouter fichier inexistant
    cursor.execute("""
        INSERT INTO files (
            scan_id, path, filename, parent_dir, size_bytes, is_directory,
            extension, owner_uid, owner_gid, owner_name, group_name,
            permissions, mtime, ctime, atime, inode, num_links,
            scan_timestamp, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        scan_id, "/nonexistent/file.txt", "file.txt", "/nonexistent",
        100, 0, "txt", 1000, 1000, "test", "test", "-rw-r--r--",
        int(time.time()), int(time.time()), int(time.time()),
        999999, 1, int(time.time()), None
    ))
    
    db.conn.commit()
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    # Ne doit pas crasher
    hash_result = detector._calculate_file_hash("/nonexistent/file.txt")
    assert hash_result is None  # Doit retourner None en cas d'erreur


def test_performance_benchmark(db_with_duplicates):
    """Test performance de la détection."""
    db, scan_id, temp_dir = db_with_duplicates
    
    detector = DuplicateDetector(db.conn, scan_id)
    
    start = time.time()
    report = detector.detect_all_duplicates(min_size=0)
    duration = time.time() - start
    
    # Doit être rapide (< 5s pour petit dataset)
    assert duration < 5.0
    
    # Vérifier temps rapporté
    assert report['execution_time'] > 0
    assert abs(report['execution_time'] - duration) < 0.5  # Tolérance
