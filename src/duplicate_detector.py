"""
Module de détection avancée de doublons.

Implémente une détection multi-niveaux :
1. Regroupement par taille
2. Hash partiel (premiers KB)
3. Hash complet pour validation finale

Supporte le calcul parallélisé des hash pour améliorer les performances.
"""

import hashlib
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
from multiprocessing import Pool, cpu_count
from functools import partial as functools_partial

logger = logging.getLogger('server_analyzer.duplicate_detector')


# ============================================================================
# FONCTIONS WORKERS POUR MULTIPROCESSING
# ============================================================================

def _calculate_hash_worker(file_path: str, partial: bool, chunk_size: int, 
                          partial_size: int) -> Tuple[str, Optional[str]]:
    """
    Worker pour calcul de hash (utilisé par multiprocessing).
    
    Args:
        file_path: Chemin du fichier
        partial: Si True, hash partiel uniquement
        chunk_size: Taille des chunks de lecture
        partial_size: Taille du hash partiel
        
    Returns:
        Tuple (file_path, hash_md5 ou None)
    """
    try:
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            if partial:
                chunk = f.read(partial_size)
                hasher.update(chunk)
            else:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
        
        return (file_path, hasher.hexdigest())
        
    except (IOError, OSError, PermissionError) as e:
        logger.warning(f"Impossible de hasher {file_path}: {e}")
        return (file_path, None)


class DuplicateDetector:
    """Détecteur de fichiers doublons avec calcul de hash."""
    
    # Taille du chunk pour lecture progressive (1 MB)
    CHUNK_SIZE = 1024 * 1024
    
    # Taille du hash partiel (premiers 8 KB)
    PARTIAL_HASH_SIZE = 8192
    
    def __init__(self, db_conn, scan_id: str, num_workers: int = None):
        """
        Initialise le détecteur.
        
        Args:
            db_conn: DatabaseManager ou connexion SQLite directe
            scan_id: ID du scan à analyser
            num_workers: Nombre de workers pour calcul parallèle (None = auto)
        """
        # Gérer DatabaseManager ou connexion directe
        if hasattr(db_conn, 'conn'):
            # C'est un DatabaseManager
            self.db_conn = db_conn.conn
        else:
            # C'est déjà une connexion SQLite
            self.db_conn = db_conn
            
        self.scan_id = scan_id
        self.num_workers = num_workers or max(1, cpu_count() - 1)
        
        logger.info(f"DuplicateDetector initialisé avec {self.num_workers} workers")
        
    def _calculate_file_hash_batch(self, file_paths: List[str], 
                                   partial: bool = False) -> Dict[str, Optional[str]]:
        """
        Calcule hash pour plusieurs fichiers en parallèle.
        
        Args:
            file_paths: Liste des chemins de fichiers
            partial: Si True, hash partiel uniquement
            
        Returns:
            Dict {file_path: hash_md5}
        """
        if not file_paths:
            return {}
        
        # Si peu de fichiers, calcul séquentiel
        if len(file_paths) < self.num_workers * 2:
            results = {}
            for path in file_paths:
                results[path] = self._calculate_file_hash(path, partial)
            return results
        
        # Calcul parallèle avec multiprocessing
        logger.info(f"Calcul parallèle de {len(file_paths)} hash avec {self.num_workers} workers")
        
        worker_func = functools_partial(
            _calculate_hash_worker,
            partial=partial,
            chunk_size=self.CHUNK_SIZE,
            partial_size=self.PARTIAL_HASH_SIZE
        )
        
        results = {}
        
        try:
            with Pool(processes=self.num_workers) as pool:
                # Map fichiers vers workers
                hash_results = pool.map(worker_func, file_paths)
                
                # Convertir en dict
                for file_path, file_hash in hash_results:
                    results[file_path] = file_hash
                    
        except Exception as e:
            logger.error(f"Erreur calcul parallèle: {e}")
            # Fallback sur calcul séquentiel
            logger.warning("Basculement sur calcul séquentiel")
            for path in file_paths:
                results[path] = self._calculate_file_hash(path, partial)
        
        return results
    
    def _calculate_file_hash(self, file_path: str, partial: bool = False) -> Optional[str]:
        """
        Calcule le hash MD5 d'un fichier (version séquentielle).
        
        Args:
            file_path: Chemin du fichier
            partial: Si True, hash seulement les premiers KB
            
        Returns:
            Hash MD5 en hexadécimal ou None en cas d'erreur
        """
        try:
            hasher = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                if partial:
                    # Hash partiel (premiers KB seulement)
                    chunk = f.read(self.PARTIAL_HASH_SIZE)
                    hasher.update(chunk)
                else:
                    # Hash complet par chunks
                    while True:
                        chunk = f.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except (IOError, OSError, PermissionError) as e:
            logger.warning(f"Impossible de hasher {file_path}: {e}")
            return None
    
    def find_duplicates_by_size(self, min_size: int = 0) -> List[Dict[str, Any]]:
        """
        Première étape : regroupe fichiers par taille.
        
        Args:
            min_size: Taille minimale en octets (ignorer petits fichiers)
            
        Returns:
            Liste de groupes de fichiers ayant la même taille
        """
        cursor = self.db_conn.cursor()
        
        cursor.execute("""
            SELECT 
                size_bytes,
                COUNT(*) as count,
                GROUP_CONCAT(path, '|||') as paths,
                GROUP_CONCAT(filename, '|||') as filenames
            FROM files
            WHERE scan_id = ?
              AND is_directory = 0
              AND size_bytes >= ?
            GROUP BY size_bytes
            HAVING count > 1
            ORDER BY size_bytes DESC
        """, (self.scan_id, min_size))
        
        groups = []
        for row in cursor.fetchall():
            size_bytes, count, paths_str, filenames_str = row
            
            paths = paths_str.split('|||') if paths_str else []
            filenames = filenames_str.split('|||') if filenames_str else []
            
            groups.append({
                'size_bytes': size_bytes,
                'count': count,
                'paths': paths,
                'filenames': filenames
            })
        
        logger.info(f"Trouvé {len(groups)} groupes de fichiers de même taille")
        return groups
    
    def find_duplicates_by_partial_hash(self, size_groups: List[Dict]) -> List[Dict[str, Any]]:
        """
        Deuxième étape : calcule hash partiel pour affiner (version parallélisée).
        
        Args:
            size_groups: Groupes de fichiers de même taille
            
        Returns:
            Liste de groupes avec même hash partiel
        """
        hash_groups = {}
        total_files = sum(len(g['paths']) for g in size_groups)
        
        logger.info(f"Calcul hash partiel pour {total_files} fichiers")
        
        for group in size_groups:
            size = group['size_bytes']
            paths = group['paths']
            
            # Calculer hash partiel en parallèle pour tous les fichiers du groupe
            hash_results = self._calculate_file_hash_batch(paths, partial=True)
            
            for path, partial_hash in hash_results.items():
                if partial_hash:
                    # Clé = taille + hash partiel
                    key = f"{size}_{partial_hash}"
                    
                    if key not in hash_groups:
                        hash_groups[key] = {
                            'size_bytes': size,
                            'partial_hash': partial_hash,
                            'paths': []
                        }
                    
                    hash_groups[key]['paths'].append(path)
        
        # Filtrer : garder seulement groupes avec 2+ fichiers
        result = [
            group for group in hash_groups.values()
            if len(group['paths']) > 1
        ]
        
        logger.info(f"Trouvé {len(result)} groupes avec hash partiel identique")
        return result
    
    def find_duplicates_by_full_hash(self, partial_groups: List[Dict]) -> List[Dict[str, Any]]:
        """
        Troisième étape : validation finale avec hash complet (version parallélisée).
        
        Args:
            partial_groups: Groupes avec même hash partiel
            
        Returns:
            Liste de groupes de vrais doublons (hash complet identique)
        """
        hash_groups = {}
        total_files = sum(len(g['paths']) for g in partial_groups)
        
        logger.info(f"Calcul hash complet pour {total_files} fichiers")
        
        for group in partial_groups:
            size = group['size_bytes']
            paths = group['paths']
            
            # Calculer hash complet en parallèle pour tous les fichiers du groupe
            hash_results = self._calculate_file_hash_batch(paths, partial=False)
            
            for path, full_hash in hash_results.items():
                if full_hash:
                    # Clé = taille + hash complet
                    key = f"{size}_{full_hash}"
                    
                    if key not in hash_groups:
                        hash_groups[key] = {
                            'size_bytes': size,
                            'hash': full_hash,
                            'paths': [],
                            'count': 0
                        }
                    
                    hash_groups[key]['paths'].append(path)
                    hash_groups[key]['count'] += 1
        
        # Filtrer : garder seulement vrais doublons
        result = [
            group for group in hash_groups.values()
            if group['count'] > 1
        ]
        
        logger.info(f"Trouvé {len(result)} groupes de vrais doublons")
        return result
    
    def detect_all_duplicates(self, min_size: int = 1024, 
                             use_partial_hash: bool = True,
                             use_cache: bool = True,
                             save_to_cache: bool = True) -> Dict[str, Any]:
        """
        Détection complète de doublons (pipeline complet) avec cache.
        
        Args:
            min_size: Taille minimale en octets (défaut 1 KB)
            use_partial_hash: Utiliser hash partiel comme optimisation
            use_cache: Utiliser le cache si disponible
            save_to_cache: Sauvegarder résultats dans le cache
            
        Returns:
            Dict avec statistiques et groupes de doublons
        """
        start_time = time.time()
        
        logger.info(f"Début détection doublons (min_size={min_size} bytes)")
        
        # Vérifier cache si activé
        if use_cache:
            cached_groups = self._get_from_cache(min_size)
            if cached_groups is not None:
                logger.info("✅ Résultats récupérés depuis le cache")
                return self._build_report(cached_groups, time.time() - start_time, from_cache=True)
        
        # Étape 1 : Grouper par taille
        size_groups = self.find_duplicates_by_size(min_size)
        
        if not size_groups:
            return {
                'duplicate_groups': [],
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0,
                'execution_time': time.time() - start_time,
                'from_cache': False
            }
        
        # Étape 2 : Hash partiel (optionnel, pour performance)
        if use_partial_hash:
            partial_groups = self.find_duplicates_by_partial_hash(size_groups)
        else:
            # Convertir directement size_groups au format attendu
            partial_groups = size_groups
        
        if not partial_groups:
            return {
                'duplicate_groups': [],
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0,
                'execution_time': time.time() - start_time,
                'from_cache': False
            }
        
        # Étape 3 : Hash complet (validation finale)
        duplicate_groups = self.find_duplicates_by_full_hash(partial_groups)
        
        # Sauvegarder dans le cache si activé
        if save_to_cache and duplicate_groups:
            self._save_to_cache(duplicate_groups, min_size)
        
        # Construire rapport
        return self._build_report(duplicate_groups, time.time() - start_time, from_cache=False)
    
    def _get_from_cache(self, min_size: int) -> Optional[List[Dict]]:
        """
        Récupère les doublons depuis le cache de la base de données.
        
        Args:
            min_size: Taille minimale
            
        Returns:
            Liste des groupes ou None si pas de cache valide
        """
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    hash_md5, size_bytes, file_count, file_paths,
                    min_size_config
                FROM duplicate_groups
                WHERE scan_id = ?
            """, (self.scan_id,))
            
            rows = cursor.fetchall()
            
            if not rows:
                logger.info("Pas de cache disponible")
                return None
            
            # Vérifier compatibilité min_size
            cached_min_size = rows[0][4] if rows[0][4] is not None else 0
            if min_size > cached_min_size:
                logger.info(
                    f"Cache incompatible: min_size demandé ({min_size}) > "
                    f"cached ({cached_min_size})"
                )
                return None
            
            # Reconstruire groupes
            groups = []
            for row in rows:
                hash_md5, size_bytes, file_count, paths_str, _ = row
                
                # Filtrer par min_size si nécessaire
                if size_bytes < min_size:
                    continue
                
                paths = paths_str.split('|||') if paths_str else []
                
                groups.append({
                    'hash': hash_md5,
                    'size_bytes': size_bytes,
                    'count': file_count,
                    'paths': paths
                })
            
            logger.info(f"✅ {len(groups)} groupes récupérés depuis cache")
            return groups
            
        except Exception as e:
            logger.warning(f"Erreur lecture cache: {e}")
            return None
    
    def _save_to_cache(self, groups: List[Dict], min_size: int):
        """
        Sauvegarde les groupes de doublons dans le cache.
        
        Args:
            groups: Liste des groupes
            min_size: Taille minimale utilisée
        """
        try:
            cursor = self.db_conn.cursor()
            timestamp = int(time.time())
            
            # Supprimer ancien cache
            cursor.execute("""
                DELETE FROM duplicate_groups WHERE scan_id = ?
            """, (self.scan_id,))
            
            # Insérer nouveaux groupes
            for group in groups:
                paths_str = '|||'.join(group.get('paths', []))
                
                cursor.execute("""
                    INSERT INTO duplicate_groups (
                        scan_id, hash_md5, size_bytes, file_count,
                        file_paths, detection_timestamp, min_size_config
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.scan_id,
                    group['hash'],
                    group['size_bytes'],
                    group['count'],
                    paths_str,
                    timestamp,
                    min_size
                ))
            
            self.db_conn.commit()
            logger.info(f"✅ {len(groups)} groupes sauvegardés dans le cache")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _build_report(self, groups: List[Dict], execution_time: float, 
                     from_cache: bool = False) -> Dict[str, Any]:
        """
        Construit le rapport final de détection.
        
        Args:
            groups: Liste des groupes de doublons
            execution_time: Temps d'exécution
            from_cache: Si les résultats viennent du cache
            
        Returns:
            Rapport complet
        """
        # Calculer statistiques
        total_duplicates = 0
        wasted_space = 0
        
        for group in groups:
            # Nombre de copies superflues = total - 1 (garder 1 original)
            redundant_copies = group['count'] - 1
            total_duplicates += redundant_copies
            wasted_space += group['size_bytes'] * redundant_copies
        
        logger.info(f"Détection terminée en {execution_time:.2f}s")
        logger.info(f"  - {len(groups)} groupes de doublons")
        logger.info(f"  - {total_duplicates} fichiers en double")
        logger.info(f"  - {wasted_space / (1024**3):.2f} GB d'espace gaspillé")
        if from_cache:
            logger.info(f"  - 🚀 Résultats depuis cache (gain de temps!)")
        
        return {
            'duplicate_groups': groups,
            'total_groups': len(groups),
            'total_duplicates': total_duplicates,
            'wasted_space': wasted_space,
            'execution_time': execution_time,
            'from_cache': from_cache
        }
    
    def get_duplicate_details(self, duplicate_groups: List[Dict]) -> List[Dict[str, Any]]:
        """
        Enrichit les groupes de doublons avec métadonnées complètes.
        
        Args:
            duplicate_groups: Groupes de doublons (hash identique)
            
        Returns:
            Liste enrichie avec métadonnées pour chaque fichier
        """
        cursor = self.db_conn.cursor()
        enriched_groups = []
        
        for group in duplicate_groups:
            paths = group['paths']
            
            # Récupérer métadonnées pour chaque fichier
            placeholders = ','.join(['?'] * len(paths))
            query = f"""
                SELECT 
                    path,
                    filename,
                    size_bytes,
                    owner_name,
                    mtime,
                    ctime,
                    permissions,
                    parent_dir
                FROM files
                WHERE scan_id = ?
                  AND path IN ({placeholders})
                ORDER BY mtime ASC
            """
            
            cursor.execute(query, [self.scan_id] + paths)
            
            files_details = []
            for row in cursor.fetchall():
                files_details.append({
                    'path': row[0],
                    'filename': row[1],
                    'size_bytes': row[2],
                    'owner': row[3],
                    'mtime': row[4],
                    'ctime': row[5],
                    'permissions': row[6],
                    'parent_dir': row[7]
                })
            
            enriched_groups.append({
                'hash': group['hash'],
                'size_bytes': group['size_bytes'],
                'count': group['count'],
                'files': files_details,
                # Le plus ancien = original probable
                'oldest_file': files_details[0]['path'] if files_details else None
            })
        
        return enriched_groups


def find_duplicates_quick(scan_id: str, db_conn: sqlite3.Connection, 
                         min_size: int = 1024) -> Dict[str, Any]:
    """
    Fonction helper pour détection rapide de doublons.
    
    Args:
        scan_id: ID du scan
        db_conn: Connexion base de données
        min_size: Taille minimale en octets
        
    Returns:
        Résultats de détection avec statistiques
    """
    detector = DuplicateDetector(db_conn, scan_id)
    return detector.detect_all_duplicates(min_size=min_size)


def get_duplicate_report(scan_id: str, db_conn: sqlite3.Connection,
                        min_size: int = 1024) -> Dict[str, Any]:
    """
    Génère un rapport complet de doublons avec détails.
    
    Args:
        scan_id: ID du scan
        db_conn: Connexion base de données
        min_size: Taille minimale en octets
        
    Returns:
        Rapport complet avec groupes enrichis
    """
    detector = DuplicateDetector(db_conn, scan_id)
    
    # Détection
    results = detector.detect_all_duplicates(min_size=min_size)
    
    # Enrichissement
    if results['duplicate_groups']:
        enriched = detector.get_duplicate_details(results['duplicate_groups'])
        results['duplicate_groups'] = enriched
    
    return results
