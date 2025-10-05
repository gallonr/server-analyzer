"""
Module de scan du système de fichiers.

Implémente le scan parallélisé avec extraction de métadonnées.
"""

import os
import stat
import pwd
import grp
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from multiprocessing import Pool, Queue, Manager
from queue import Empty
import threading

logger = logging.getLogger('server_analyzer.scanner')


class FileScanner:
    """Scanner de fichiers avec extraction de métadonnées."""
    
    def __init__(self, scan_id: str, exclusions: dict = None):
        """
        Initialise le scanner.
        
        Args:
            scan_id: ID du scan en cours
            exclusions: Configuration des exclusions (directories, extensions)
        """
        self.scan_id = scan_id
        self.exclusions = exclusions or {'directories': [], 'extensions': []}
        self.errors_count = 0
        
    def extract_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Extrait les métadonnées d'un fichier ou dossier.
        
        Args:
            path: Chemin absolu du fichier/dossier
            
        Returns:
            Dict avec métadonnées ou None en cas d'erreur
        """
        try:
            # Utiliser lstat pour ne pas suivre les liens symboliques
            stat_info = os.lstat(path)
            
            # Informations de base
            is_directory = stat.S_ISDIR(stat_info.st_mode)
            filename = os.path.basename(path)
            parent_dir = os.path.dirname(path)
            
            # Extension (seulement pour fichiers)
            extension = None
            if not is_directory:
                _, ext = os.path.splitext(filename)
                extension = ext[1:].lower() if ext else ''
            
            # Propriétaire
            try:
                owner_name = pwd.getpwuid(stat_info.st_uid).pw_name
            except (KeyError, AttributeError):
                owner_name = str(stat_info.st_uid)
            
            # Groupe
            try:
                group_name = grp.getgrgid(stat_info.st_gid).gr_name
            except (KeyError, AttributeError):
                group_name = str(stat_info.st_gid)
            
            # Permissions en format lisible (rwxr-xr-x)
            permissions = stat.filemode(stat_info.st_mode)
            
            # Construire le dictionnaire de métadonnées
            metadata = {
                'scan_id': self.scan_id,
                'path': path,
                'filename': filename,
                'parent_dir': parent_dir,
                'size_bytes': stat_info.st_size,
                'is_directory': 1 if is_directory else 0,
                'extension': extension,
                'owner_uid': str(stat_info.st_uid),
                'owner_gid': str(stat_info.st_gid),
                'owner_name': owner_name,
                'group_name': group_name,
                'permissions': permissions,
                'mtime': int(stat_info.st_mtime),
                'ctime': int(stat_info.st_ctime),
                'atime': int(stat_info.st_atime),
                'inode': str(stat_info.st_ino),
                'num_links': stat_info.st_nlink,
                'scan_timestamp': int(time.time()),
                'error_message': None
            }
            
            return metadata
            
        except PermissionError:
            logger.warning(f"Permission refusée: {path}")
            self.errors_count += 1
            return self._create_error_metadata(path, "Permission refusée")
        except FileNotFoundError:
            logger.warning(f"Fichier introuvable: {path}")
            self.errors_count += 1
            return self._create_error_metadata(path, "Fichier introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction métadonnées pour {path}: {e}")
            self.errors_count += 1
            return self._create_error_metadata(path, str(e))
    
    def _create_error_metadata(self, path: str, error_msg: str) -> Dict[str, Any]:
        """
        Crée un enregistrement de métadonnées pour un fichier en erreur.
        
        Args:
            path: Chemin du fichier
            error_msg: Message d'erreur
            
        Returns:
            Dict avec métadonnées minimales et message d'erreur
        """
        return {
            'scan_id': self.scan_id,
            'path': path,
            'filename': os.path.basename(path),
            'parent_dir': os.path.dirname(path),
            'size_bytes': 0,
            'is_directory': 0,
            'extension': None,
            'owner_uid': None,
            'owner_gid': None,
            'owner_name': None,
            'group_name': None,
            'permissions': None,
            'mtime': None,
            'ctime': None,
            'atime': None,
            'inode': None,
            'num_links': None,
            'scan_timestamp': int(time.time()),
            'error_message': error_msg
        }
    
    def should_exclude(self, path: str) -> bool:
        """
        Vérifie si un chemin doit être exclu.
        
        Args:
            path: Chemin à vérifier
            
        Returns:
            True si doit être exclu
        """
        from src.utils import is_excluded
        return is_excluded(path, self.exclusions)


def scan_directory_worker(args: tuple) -> List[Dict[str, Any]]:
    """
    Worker function pour scanner un répertoire (utilisé par multiprocessing).
    
    Args:
        args: Tuple (directory_path, scan_id, exclusions, visited_inodes)
        
    Returns:
        Liste des métadonnées extraites
    """
    directory_path, scan_id, exclusions, visited_inodes = args
    
    scanner = FileScanner(scan_id, exclusions)
    results = []
    
    try:
        # Scanner le répertoire avec os.scandir (plus rapide que listdir)
        with os.scandir(directory_path) as entries:
            for entry in entries:
                try:
                    # Éviter les boucles infinies avec les liens symboliques
                    if entry.is_symlink():
                        stat_info = entry.stat(follow_symlinks=False)
                        if stat_info.st_ino in visited_inodes:
                            logger.debug(f"Lien symbolique circulaire détecté: {entry.path}")
                            continue
                        visited_inodes.add(stat_info.st_ino)
                    
                    # Vérifier exclusions
                    if scanner.should_exclude(entry.path):
                        logger.debug(f"Chemin exclu: {entry.path}")
                        continue
                    
                    # Extraire métadonnées
                    metadata = scanner.extract_metadata(entry.path)
                    if metadata:
                        results.append(metadata)
                    
                except Exception as e:
                    logger.error(f"Erreur traitement {entry.path}: {e}")
                    continue
                    
    except PermissionError:
        logger.warning(f"Permission refusée pour le répertoire: {directory_path}")
    except Exception as e:
        logger.error(f"Erreur scan répertoire {directory_path}: {e}")
    
    return results


class ParallelScanner:
    """Scanner parallélisé avec multiprocessing."""
    
    def __init__(self, scan_id: str, num_workers: int, 
                 exclusions: dict = None, batch_size: int = 50000):
        """
        Initialise le scanner parallélisé.
        
        Args:
            scan_id: ID du scan
            num_workers: Nombre de workers parallèles
            exclusions: Configuration des exclusions
            batch_size: Taille des lots pour insertion DB
        """
        self.scan_id = scan_id
        self.num_workers = num_workers
        self.exclusions = exclusions or {'directories': [], 'extensions': []}
        self.batch_size = batch_size
        self.files_scanned = 0
        self.directories_to_scan: List[str] = []
        self.visited_inodes: Set[int] = set()
        
    def discover_directories(self, root_paths: List[str]) -> List[str]:
        """
        Découvre tous les sous-répertoires à scanner.
        
        Args:
            root_paths: Liste des chemins racine
            
        Returns:
            Liste de tous les répertoires à scanner
        """
        directories = []
        scanner = FileScanner(self.scan_id, self.exclusions)
        
        for root_path in root_paths:
            if not os.path.exists(root_path):
                logger.warning(f"Chemin racine n'existe pas: {root_path}")
                continue
            
            logger.info(f"Découverte de l'arborescence: {root_path}")
            
            # Parcours récursif pour découvrir tous les répertoires
            for dirpath, dirnames, _ in os.walk(root_path, followlinks=False):
                # Filtrer les répertoires exclus
                dirnames[:] = [d for d in dirnames 
                              if not scanner.should_exclude(os.path.join(dirpath, d))]
                
                directories.append(dirpath)
                
                if len(directories) % 1000 == 0:
                    logger.info(f"Répertoires découverts: {len(directories)}")
        
        logger.info(f"Découverte terminée: {len(directories)} répertoires à scanner")
        return directories
    
    def scan(self, root_paths: List[str], db_manager, 
             checkpoint_interval: int = 300) -> Dict[str, Any]:
        """
        Lance le scan parallélisé complet.
        
        Args:
            root_paths: Liste des chemins racine
            db_manager: Instance de DatabaseManager pour insertion
            checkpoint_interval: Intervalle en secondes entre checkpoints
            
        Returns:
            Statistiques du scan
        """
        start_time = time.time()
        
        # Découvrir tous les répertoires
        logger.info("Phase 1: Découverte de l'arborescence")
        self.directories_to_scan = self.discover_directories(root_paths)
        
        if not self.directories_to_scan:
            logger.error("Aucun répertoire à scanner")
            return {'files_scanned': 0, 'errors': 0}
        
        # Préparer les arguments pour les workers
        manager = Manager()
        shared_visited = manager.list(self.visited_inodes)
        
        worker_args = [
            (directory, self.scan_id, self.exclusions, shared_visited)
            for directory in self.directories_to_scan
        ]
        
        # Lancer le scan parallélisé
        logger.info(f"Phase 2: Scan parallélisé avec {self.num_workers} workers")
        logger.info(f"Répertoires à traiter: {len(self.directories_to_scan)}")
        
        batch_buffer = []
        total_errors = 0
        last_checkpoint = time.time()
        
        with Pool(processes=self.num_workers) as pool:
            # imap_unordered pour traiter les résultats dès qu'ils arrivent
            for results in pool.imap_unordered(scan_directory_worker, worker_args, chunksize=10):
                batch_buffer.extend(results)
                self.files_scanned += len(results)
                
                # Insertion par lots
                if len(batch_buffer) >= self.batch_size:
                    db_manager.batch_insert_files(batch_buffer)
                    logger.info(f"Progression: {self.files_scanned} fichiers scannés")
                    batch_buffer = []
                
                # Checkpoint périodique
                if time.time() - last_checkpoint > checkpoint_interval:
                    self._save_checkpoint(db_manager)
                    last_checkpoint = time.time()
        
        # Insérer le dernier lot
        if batch_buffer:
            db_manager.batch_insert_files(batch_buffer)
        
        end_time = time.time()
        duration = end_time - start_time
        
        stats = {
            'files_scanned': self.files_scanned,
            'directories_scanned': len(self.directories_to_scan),
            'duration_seconds': duration,
            'files_per_second': self.files_scanned / duration if duration > 0 else 0,
            'errors': total_errors
        }
        
        logger.info(f"Scan terminé: {stats}")
        return stats
    
    def _save_checkpoint(self, db_manager):
        """
        Sauvegarde un checkpoint de progression.
        
        Args:
            db_manager: Instance DatabaseManager
        """
        total_size = db_manager.get_total_size(self.scan_id)
        db_manager.update_scan_status(
            self.scan_id,
            'running',
            total_files=self.files_scanned,
            total_size=total_size
        )
        logger.info(f"Checkpoint sauvegardé: {self.files_scanned} fichiers")
