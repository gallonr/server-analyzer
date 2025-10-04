"""
Module de calcul des statistiques et agrégations.

Ce module fournit des fonctions pour calculer des statistiques agrégées
sur les données scannées et détecter des anomalies.
"""

import sqlite3
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger('server_analyzer.stats')


def compute_directory_stats(scan_id: str, db_conn: sqlite3.Connection) -> int:
    """
    Calcule les statistiques par dossier.
    
    Args:
        scan_id: Identifiant du scan
        db_conn: Connexion SQLite
        
    Returns:
        Nombre de dossiers traités
    """
    cursor = db_conn.cursor()
    
    # Récupérer tous les dossiers uniques
    cursor.execute("""
        SELECT DISTINCT parent_dir 
        FROM files 
        WHERE scan_id = ?
    """, (scan_id,))
    
    directories = [row[0] for row in cursor.fetchall()]
    logger.info(f"Traitement de {len(directories)} dossiers")
    
    processed = 0
    
    for dir_path in directories:
        # Statistiques du dossier
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE is_directory = 0) as total_files,
                COUNT(*) FILTER (WHERE is_directory = 1) as total_dirs,
                SUM(size_bytes) as total_size,
                MIN(mtime) as oldest_mtime,
                MAX(mtime) as newest_mtime
            FROM files
            WHERE parent_dir = ? AND scan_id = ?
        """, (dir_path, scan_id))
        
        row = cursor.fetchone()
        total_files = row[0] or 0
        total_dirs = row[1] or 0
        total_size = row[2] or 0
        oldest_mtime = row[3]
        newest_mtime = row[4]
        
        # Répartition par extension
        cursor.execute("""
            SELECT extension, COUNT(*), SUM(size_bytes)
            FROM files
            WHERE parent_dir = ? AND scan_id = ? AND is_directory = 0
            GROUP BY extension
        """, (dir_path, scan_id))
        
        file_count_by_ext = {}
        size_by_ext = {}
        for ext_row in cursor.fetchall():
            ext = ext_row[0] or 'no_ext'
            file_count_by_ext[ext] = ext_row[1]
            size_by_ext[ext] = ext_row[2]
        
        # Distribution propriétaires
        cursor.execute("""
            SELECT owner_name, COUNT(*)
            FROM files
            WHERE parent_dir = ? AND scan_id = ? AND is_directory = 0
            GROUP BY owner_name
        """, (dir_path, scan_id))
        
        owner_distribution = {}
        for owner_row in cursor.fetchall():
            owner = owner_row[0] or 'unknown'
            owner_distribution[owner] = owner_row[1]
        
        # Insertion dans directory_stats
        cursor.execute("""
            INSERT OR REPLACE INTO directory_stats (
                dir_path, total_files, total_directories, total_size_bytes,
                extension_stats, owner_stats,
                oldest_file_mtime, newest_file_mtime,
                scan_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dir_path,
            total_files,
            total_dirs,
            total_size,
            json.dumps(file_count_by_ext),
            json.dumps(owner_distribution),
            oldest_mtime,
            newest_mtime,
            scan_id,
            int(time.time())
        ))
        
        processed += 1
        
        if processed % 100 == 0:
            logger.info(f"Traité {processed}/{len(directories)} dossiers")
    
    db_conn.commit()
    logger.info(f"Statistiques calculées pour {processed} dossiers")
    
    return processed


def compute_extension_stats(scan_id: str, db_conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calcule statistiques par extension.
    
    Args:
        scan_id: Identifiant du scan
        db_conn: Connexion SQLite
        
    Returns:
        Dictionnaire : {extension: {count, total_size, avg_size}}
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT 
            extension,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size,
            AVG(size_bytes) as avg_size,
            MIN(size_bytes) as min_size,
            MAX(size_bytes) as max_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY extension
        ORDER BY total_size DESC
    """, (scan_id,))
    
    stats = {}
    
    for row in cursor.fetchall():
        ext = row[0] or 'no_extension'
        stats[ext] = {
            'count': row[1],
            'total_size': row[2],
            'avg_size': round(row[3], 2) if row[3] else 0,
            'min_size': row[4],
            'max_size': row[5]
        }
    
    logger.info(f"Statistiques calculées pour {len(stats)} extensions")
    
    return stats


def get_top_extensions(scan_id: str, db_conn: sqlite3.Connection, 
                       limit: int = 10, by: str = 'size') -> List[Tuple]:
    """
    Récupère top N extensions.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        limit: Nombre d'extensions
        by: Tri par 'size' ou 'count'
        
    Returns:
        Liste de tuples (extension, count, total_size)
    """
    cursor = db_conn.cursor()
    
    order_by = "total_size DESC" if by == 'size' else "file_count DESC"
    
    cursor.execute(f"""
        SELECT 
            extension,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY extension
        ORDER BY {order_by}
        LIMIT ?
    """, (scan_id, limit))
    
    return cursor.fetchall()


def compute_owner_stats(scan_id: str, db_conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calcule statistiques par propriétaire.
    
    Args:
        scan_id: Identifiant du scan
        db_conn: Connexion SQLite
        
    Returns:
        Dictionnaire : {owner: {count, total_size}}
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT 
            owner_name,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY owner_name
        ORDER BY total_size DESC
    """, (scan_id,))
    
    stats = {}
    
    for row in cursor.fetchall():
        owner = row[0] or 'unknown'
        stats[owner] = {
            'count': row[1],
            'total_size': row[2]
        }
    
    logger.info(f"Statistiques calculées pour {len(stats)} propriétaires")
    
    return stats


def get_top_owners(scan_id: str, db_conn: sqlite3.Connection, 
                   limit: int = 10) -> List[Tuple]:
    """
    Récupère top N propriétaires par volume.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        limit: Nombre de propriétaires
        
    Returns:
        Liste de tuples (owner, count, total_size)
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT 
            owner_name,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY owner_name
        ORDER BY total_size DESC
        LIMIT ?
    """, (scan_id, limit))
    
    return cursor.fetchall()


def compute_temporal_distribution(scan_id: str, db_conn: sqlite3.Connection,
                                 groupby: str = 'month') -> Dict[str, Any]:
    """
    Calcule distribution temporelle des fichiers.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        groupby: 'month', 'year', 'day'
        
    Returns:
        Dictionnaire {period: {count, total_size}}
    """
    cursor = db_conn.cursor()
    
    # Format selon groupby
    if groupby == 'month':
        format_str = '%Y-%m'
    elif groupby == 'year':
        format_str = '%Y'
    elif groupby == 'day':
        format_str = '%Y-%m-%d'
    else:
        raise ValueError(f"groupby invalide: {groupby}")
    
    cursor.execute(f"""
        SELECT 
            strftime('{format_str}', datetime(mtime, 'unixepoch')) as period,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY period
        ORDER BY period DESC
    """, (scan_id,))
    
    distribution = {}
    
    for row in cursor.fetchall():
        period = row[0]
        distribution[period] = {
            'count': row[1],
            'total_size': row[2]
        }
    
    return distribution


def get_oldest_newest_files(scan_id: str, db_conn: sqlite3.Connection,
                            limit: int = 10) -> Dict[str, List[Dict]]:
    """
    Récupère les fichiers les plus anciens et récents.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        limit: Nombre de fichiers à retourner
        
    Returns:
        {'oldest': [...], 'newest': [...]}
    """
    cursor = db_conn.cursor()
    
    # Plus anciens
    cursor.execute("""
        SELECT path, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        ORDER BY mtime ASC
        LIMIT ?
    """, (scan_id, limit))
    
    oldest = []
    for row in cursor.fetchall():
        oldest.append({
            'path': row[0],
            'size_bytes': row[1],
            'owner_name': row[2],
            'mtime': row[3]
        })
    
    # Plus récents
    cursor.execute("""
        SELECT path, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        ORDER BY mtime DESC
        LIMIT ?
    """, (scan_id, limit))
    
    newest = []
    for row in cursor.fetchall():
        newest.append({
            'path': row[0],
            'size_bytes': row[1],
            'owner_name': row[2],
            'mtime': row[3]
        })
    
    return {'oldest': oldest, 'newest': newest}


def detect_large_files(scan_id: str, db_conn: sqlite3.Connection,
                      threshold: int) -> List[Dict]:
    """
    Détecte fichiers volumineux.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        threshold: Seuil taille (bytes)
        
    Returns:
        Liste de fichiers > seuil
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT path, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ? 
          AND is_directory = 0
          AND size_bytes > ?
        ORDER BY size_bytes DESC
    """, (scan_id, threshold))
    
    files = []
    for row in cursor.fetchall():
        files.append({
            'path': row[0],
            'size_bytes': row[1],
            'owner_name': row[2],
            'mtime': row[3]
        })
    
    logger.info(f"Détecté {len(files)} fichiers > {threshold} bytes")
    
    return files


def detect_old_files(scan_id: str, db_conn: sqlite3.Connection,
                    days_threshold: int) -> List[Dict]:
    """
    Détecte fichiers anciens non modifiés.
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        days_threshold: Nombre de jours
        
    Returns:
        Liste de fichiers non modifiés depuis N jours
    """
    cursor = db_conn.cursor()
    
    # Calcul timestamp limite
    limit_timestamp = int(time.time()) - (days_threshold * 86400)
    
    cursor.execute("""
        SELECT path, size_bytes, owner_name, mtime
        FROM files
        WHERE scan_id = ? 
          AND is_directory = 0
          AND mtime < ?
        ORDER BY mtime ASC
    """, (scan_id, limit_timestamp))
    
    files = []
    for row in cursor.fetchall():
        files.append({
            'path': row[0],
            'size_bytes': row[1],
            'owner_name': row[2],
            'mtime': row[3]
        })
    
    logger.info(f"Détecté {len(files)} fichiers > {days_threshold} jours")
    
    return files


def detect_duplicate_candidates(scan_id: str, db_conn: sqlite3.Connection) -> List[Dict]:
    """
    Détecte doublons potentiels (même taille + même nom).
    
    Args:
        scan_id: Identifiant scan
        db_conn: Connexion SQLite
        
    Returns:
        Liste de groupes de doublons potentiels
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT filename, size_bytes, COUNT(*) as count, GROUP_CONCAT(path, '|') as paths
        FROM files
        WHERE scan_id = ? AND is_directory = 0
        GROUP BY filename, size_bytes
        HAVING count > 1
        ORDER BY size_bytes DESC
    """, (scan_id,))
    
    duplicates = []
    
    for row in cursor.fetchall():
        duplicates.append({
            'name': row[0],
            'size_bytes': row[1],
            'count': row[2],
            'paths': row[3].split('|') if row[3] else []
        })
    
    logger.info(f"Détecté {len(duplicates)} groupes de doublons potentiels")
    
    return duplicates


def explain_query(db_conn: sqlite3.Connection, query: str, params: tuple = ()) -> None:
    """
    Explique le plan d'exécution d'une requête SQL.
    
    Args:
        db_conn: Connexion SQLite
        query: Requête SQL à analyser
        params: Paramètres de la requête
    """
    cursor = db_conn.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
    
    logger.info("Plan d'exécution de la requête :")
    for row in cursor.fetchall():
        logger.info(f"  {row}")


def benchmark_query(func, *args, iterations: int = 10) -> float:
    """
    Benchmark une fonction.
    
    Args:
        func: Fonction à benchmarker
        *args: Arguments de la fonction
        iterations: Nombre d'itérations
        
    Returns:
        Temps moyen d'exécution en secondes
    """
    times = []
    for i in range(iterations):
        start = time.time()
        func(*args)
        elapsed = time.time() - start
        times.append(elapsed)
        logger.debug(f"Itération {i+1}/{iterations}: {elapsed:.3f}s")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    logger.info(f"{func.__name__}: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
    
    return avg_time
