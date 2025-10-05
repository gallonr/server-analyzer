"""
Module de gestion de la base de données SQLite.

Gère le schéma, les insertions par lots et les requêtes.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid
import time

logger = logging.getLogger('server_analyzer.database')


class DatabaseManager:
    """Gestionnaire de base de données SQLite optimisé."""
    
    def __init__(self, db_path: str):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Ouvre la connexion à la base de données."""
        # Créer dossier si nécessaire
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # check_same_thread=False permet l'utilisation multi-thread (nécessaire pour Streamlit)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Configuration PRAGMA pour performance
        self._configure_pragma()
        
        logger.info(f"Connecté à la base de données: {self.db_path}")
        
    def _configure_pragma(self):
        """Configure les paramètres PRAGMA SQLite pour optimiser les performances."""
        cursor = self.conn.cursor()
        
        pragma_settings = {
            'journal_mode': 'WAL',           # Write-Ahead Logging
            'synchronous': 'NORMAL',         # Balance sécurité/performance
            'cache_size': -40000,            # 40 MB de cache
            'page_size': 4096,               # Taille page optimale
            'temp_store': 'MEMORY',          # Tables temporaires en RAM
            'mmap_size': 268435456           # 256 MB memory-mapped I/O
        }
        
        for key, value in pragma_settings.items():
            if isinstance(value, str):
                cursor.execute(f"PRAGMA {key}={value};")
            else:
                cursor.execute(f"PRAGMA {key}={value};")
        
        logger.info("PRAGMA SQLite configurés pour performance optimale")
        
    def init_schema(self):
        """Crée le schéma complet de la base de données avec index."""
        cursor = self.conn.cursor()
        
        # Table files - métadonnées de chaque fichier
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                path TEXT NOT NULL,
                filename TEXT NOT NULL,
                parent_dir TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                is_directory INTEGER NOT NULL,
                extension TEXT,
                owner_uid TEXT,
                owner_gid TEXT,
                owner_name TEXT,
                group_name TEXT,
                permissions TEXT,
                mtime INTEGER,
                ctime INTEGER,
                atime INTEGER,
                inode TEXT,
                num_links INTEGER,
                scan_timestamp INTEGER NOT NULL,
                error_message TEXT
            )
        """)
        
        # Index pour optimisation des requêtes sur files
        indexes_files = [
            "CREATE INDEX IF NOT EXISTS idx_files_scan_id ON files(scan_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_parent_dir ON files(parent_dir)",
            "CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension)",
            "CREATE INDEX IF NOT EXISTS idx_files_owner_name ON files(owner_name)",
            "CREATE INDEX IF NOT EXISTS idx_files_size_bytes ON files(size_bytes)",
            "CREATE INDEX IF NOT EXISTS idx_files_mtime ON files(mtime)",
            "CREATE INDEX IF NOT EXISTS idx_files_is_directory ON files(is_directory)",
            "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)"
        ]
        
        for index in indexes_files:
            cursor.execute(index)
        
        # Table directory_stats - statistiques pré-calculées par dossier
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directory_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                dir_path TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                total_size_bytes INTEGER NOT NULL,
                total_directories INTEGER NOT NULL,
                extension_stats TEXT,
                owner_stats TEXT,
                oldest_file_mtime INTEGER,
                newest_file_mtime INTEGER,
                avg_file_size INTEGER,
                updated_at INTEGER NOT NULL
            )
        """)
        
        # Index pour directory_stats
        indexes_dir_stats = [
            "CREATE INDEX IF NOT EXISTS idx_dir_stats_scan_id ON directory_stats(scan_id)",
            "CREATE INDEX IF NOT EXISTS idx_dir_stats_path ON directory_stats(dir_path)",
            "CREATE INDEX IF NOT EXISTS idx_dir_stats_total_size ON directory_stats(total_size_bytes)"
        ]
        
        for index in indexes_dir_stats:
            cursor.execute(index)
        
        # Table scans - historique des analyses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                start_time INTEGER NOT NULL,
                end_time INTEGER,
                status TEXT NOT NULL,
                root_paths TEXT NOT NULL,
                total_files INTEGER DEFAULT 0,
                total_size_bytes INTEGER DEFAULT 0,
                num_workers INTEGER,
                errors_count INTEGER DEFAULT 0,
                config_snapshot TEXT,
                notes TEXT
            )
        """)
        
        # Index pour scans
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_start_time 
            ON scans(start_time)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_status 
            ON scans(status)
        """)
        
        # Table duplicate_groups - cache des doublons détectés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                hash_md5 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                file_count INTEGER NOT NULL,
                file_paths TEXT NOT NULL,
                detection_timestamp INTEGER NOT NULL,
                min_size_config INTEGER,
                UNIQUE(scan_id, hash_md5)
            )
        """)
        
        # Index pour duplicate_groups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_duplicates_scan_id 
            ON duplicate_groups(scan_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_duplicates_hash 
            ON duplicate_groups(hash_md5)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_duplicates_size 
            ON duplicate_groups(size_bytes)
        """)
        
        self.conn.commit()
        logger.info("Schéma de base de données initialisé avec succès")
        
    def create_scan(self, root_paths: List[str], num_workers: int, 
                    config_snapshot: str = None) -> str:
        """
        Crée un nouveau scan dans la table scans.
        
        Args:
            root_paths: Liste des chemins racine à scanner
            num_workers: Nombre de workers utilisés
            config_snapshot: Snapshot de la configuration (JSON)
            
        Returns:
            ID du scan créé (UUID)
        """
        scan_id = str(uuid.uuid4())
        start_time = int(time.time())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scans (id, start_time, status, root_paths, num_workers, config_snapshot)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scan_id, start_time, 'running', ','.join(root_paths), num_workers, config_snapshot))
        
        self.conn.commit()
        logger.info(f"Nouveau scan créé: {scan_id}")
        
        return scan_id
    
    def update_scan_status(self, scan_id: str, status: str, 
                          total_files: int = None, total_size: int = None,
                          errors_count: int = None):
        """
        Met à jour le statut d'un scan.
        
        Args:
            scan_id: ID du scan
            status: Nouveau statut ('running', 'completed', 'failed', 'interrupted')
            total_files: Nombre total de fichiers scannés
            total_size: Taille totale en octets
            errors_count: Nombre d'erreurs rencontrées
        """
        cursor = self.conn.cursor()
        
        updates = ["status = ?"]
        params = [status]
        
        if status in ['completed', 'failed', 'interrupted']:
            updates.append("end_time = ?")
            params.append(int(time.time()))
        
        if total_files is not None:
            updates.append("total_files = ?")
            params.append(total_files)
        
        if total_size is not None:
            updates.append("total_size_bytes = ?")
            params.append(total_size)
        
        if errors_count is not None:
            updates.append("errors_count = ?")
            params.append(errors_count)
        
        params.append(scan_id)
        
        query = f"UPDATE scans SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        
        logger.info(f"Scan {scan_id} mis à jour: {status}")
    
    def batch_insert_files(self, files_data: List[Dict[str, Any]]):
        """
        Insère un lot de fichiers en une seule transaction.
        
        Args:
            files_data: Liste de dictionnaires contenant les métadonnées des fichiers
        """
        if not files_data:
            return
        
        cursor = self.conn.cursor()
        
        # Préparer les données pour l'insertion
        insert_query = """
            INSERT INTO files (
                scan_id, path, filename, parent_dir, size_bytes, is_directory,
                extension, owner_uid, owner_gid, owner_name, group_name,
                permissions, mtime, ctime, atime, inode, num_links,
                scan_timestamp, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = []
        for file_data in files_data:
            values.append((
                file_data.get('scan_id'),
                file_data.get('path'),
                file_data.get('filename'),
                file_data.get('parent_dir'),
                file_data.get('size_bytes', 0),
                file_data.get('is_directory', 0),
                file_data.get('extension'),
                file_data.get('owner_uid'),
                file_data.get('owner_gid'),
                file_data.get('owner_name'),
                file_data.get('group_name'),
                file_data.get('permissions'),
                file_data.get('mtime'),
                file_data.get('ctime'),
                file_data.get('atime'),
                file_data.get('inode'),
                file_data.get('num_links'),
                file_data.get('scan_timestamp'),
                file_data.get('error_message')
            ))
        
        cursor.executemany(insert_query, values)
        self.conn.commit()
        
        logger.debug(f"Batch insert: {len(files_data)} fichiers insérés")
    
    def get_scan_info(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un scan.
        
        Args:
            scan_id: ID du scan
            
        Returns:
            Dictionnaire avec les informations du scan ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_latest_scan_id(self) -> Optional[str]:
        """
        Récupère l'ID du scan le plus récent.
        
        Returns:
            ID du scan le plus récent ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM scans 
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if row:
            return row[0]
        return None
    
    def get_total_files_count(self, scan_id: str) -> int:
        """
        Compte le nombre total de fichiers pour un scan.
        
        Args:
            scan_id: ID du scan
            
        Returns:
            Nombre de fichiers
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM files 
            WHERE scan_id = ? AND is_directory = 0
        """, (scan_id,))
        return cursor.fetchone()[0]
    
    def get_total_size(self, scan_id: str) -> int:
        """
        Calcule la taille totale des fichiers pour un scan.
        
        Args:
            scan_id: ID du scan
            
        Returns:
            Taille totale en octets
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(size_bytes) FROM files 
            WHERE scan_id = ? AND is_directory = 0
        """, (scan_id,))
        result = cursor.fetchone()[0]
        return result if result else 0
    
    # ========================================================================
    # MÉTHODES CACHE DOUBLONS
    # ========================================================================
    
    def save_duplicate_groups(self, scan_id: str, groups: List[Dict], 
                             min_size: int = 0):
        """
        Sauvegarde les groupes de doublons en cache.
        
        Args:
            scan_id: ID du scan
            groups: Liste des groupes de doublons (avec hash)
            min_size: Taille minimale utilisée pour la détection
        """
        cursor = self.conn.cursor()
        timestamp = int(time.time())
        
        # Supprimer ancien cache pour ce scan
        cursor.execute("""
            DELETE FROM duplicate_groups WHERE scan_id = ?
        """, (scan_id,))
        
        # Insérer nouveaux groupes
        for group in groups:
            # Convertir paths en string séparé par |||
            paths_str = '|||'.join(group.get('paths', []))
            
            cursor.execute("""
                INSERT INTO duplicate_groups (
                    scan_id, hash_md5, size_bytes, file_count,
                    file_paths, detection_timestamp, min_size_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                group['hash'],
                group['size_bytes'],
                group['count'],
                paths_str,
                timestamp,
                min_size
            ))
        
        self.conn.commit()
        logger.info(f"Sauvegardé {len(groups)} groupes de doublons pour scan {scan_id}")
    
    def get_cached_duplicate_groups(self, scan_id: str, 
                                   min_size: int = 0) -> Optional[List[Dict]]:
        """
        Récupère les groupes de doublons depuis le cache.
        
        Args:
            scan_id: ID du scan
            min_size: Taille minimale (doit correspondre au cache)
            
        Returns:
            Liste des groupes ou None si pas de cache
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                hash_md5, size_bytes, file_count, file_paths,
                detection_timestamp, min_size_config
            FROM duplicate_groups
            WHERE scan_id = ?
            ORDER BY size_bytes DESC
        """, (scan_id,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return None
        
        # Reconstruire les groupes
        groups = []
        for row in rows:
            hash_md5, size_bytes, file_count, paths_str, timestamp, cached_min_size = row
            
            # Vérifier compatibilité min_size
            # Si min_size demandé > cached, le cache n'est pas valide
            if min_size > (cached_min_size or 0):
                logger.warning(
                    f"Cache invalide: min_size demandé ({min_size}) > "
                    f"cached ({cached_min_size})"
                )
                return None
            
            paths = paths_str.split('|||') if paths_str else []
            
            groups.append({
                'hash': hash_md5,
                'size_bytes': size_bytes,
                'count': file_count,
                'paths': paths
            })
        
        logger.info(f"Récupéré {len(groups)} groupes depuis cache pour scan {scan_id}")
        return groups
    
    def get_duplicate_cache_info(self, scan_id: str) -> Optional[Dict]:
        """
        Récupère les infos sur le cache de doublons.
        
        Args:
            scan_id: ID du scan
            
        Returns:
            Dict avec infos ou None si pas de cache
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as group_count,
                MIN(detection_timestamp) as timestamp,
                MIN(min_size_config) as min_size
            FROM duplicate_groups
            WHERE scan_id = ?
        """, (scan_id,))
        
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            return None
        
        return {
            'group_count': row[0],
            'timestamp': row[1],
            'min_size': row[2] or 0
        }
    
    def clear_duplicate_cache(self, scan_id: str = None):
        """
        Efface le cache des doublons.
        
        Args:
            scan_id: ID du scan (None = tout effacer)
        """
        cursor = self.conn.cursor()
        
        if scan_id:
            cursor.execute("""
                DELETE FROM duplicate_groups WHERE scan_id = ?
            """, (scan_id,))
            logger.info(f"Cache doublons effacé pour scan {scan_id}")
        else:
            cursor.execute("DELETE FROM duplicate_groups")
            logger.info("Cache doublons effacé (tous les scans)")
        
        self.conn.commit()
    
    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion à la base de données fermée")
