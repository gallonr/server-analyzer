#!/bin/bash

# Script de migration de la base de données
# Ajoute la table duplicate_groups pour le cache de doublons

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        MIGRATION BASE DE DONNÉES - CACHE DOUBLONS           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier environnement virtuel
if [ ! -f "venv/bin/activate" ] && [ ! -f "../.venv/bin/activate" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "   Exécutez: python3 -m venv venv && source venv/bin/activate"
    exit 1
fi

# Activer environnement
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    source ../.venv/bin/activate
fi

echo "✅ Environnement virtuel activé"
echo ""

# Déterminer base de données
DB_PATH="${1:-data/server_analysis.db}"

if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Base de données non trouvée: $DB_PATH"
    echo "   Une nouvelle base sera créée"
fi

echo "Migration de: $DB_PATH"
echo ""

# Exécuter migration
python3 << PYTHON_MIGRATION
from src.database import DatabaseManager
import sys

db_path = '$DB_PATH'
print(f'📊 Base de données: {db_path}')
print()

try:
    db = DatabaseManager(db_path)
    db.connect()
    
    # Vérifier si la table existe déjà
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='duplicate_groups'
    """)
    exists_before = cursor.fetchone()
    
    if exists_before:
        print('ℹ️  La table duplicate_groups existe déjà')
    else:
        print('➕ Création de la table duplicate_groups...')
    
    # Initialiser schéma (CREATE IF NOT EXISTS)
    db.init_schema()
    
    # Vérifier après migration
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='duplicate_groups'
    """)
    exists_after = cursor.fetchone()
    
    if exists_after:
        if not exists_before:
            print('✅ Table duplicate_groups créée avec succès')
        
        # Compter les entrées
        cursor.execute("SELECT COUNT(*) FROM duplicate_groups")
        count = cursor.fetchone()[0]
        print(f'📦 Entrées dans le cache: {count}')
        print()
        
        # Vérifier les index
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='duplicate_groups'
            ORDER BY name
        """)
        indexes = cursor.fetchall()
        print(f'✅ Index créés ({len(indexes)}):')
        for idx in indexes:
            print(f'   - {idx[0]}')
        print()
        
        # Vérifier les colonnes
        cursor.execute("PRAGMA table_info(duplicate_groups)")
        columns = cursor.fetchall()
        print(f'✅ Colonnes ({len(columns)}):')
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = " [PK]" if col[5] else ""
            is_notnull = " [NOT NULL]" if col[3] else ""
            print(f'   - {col_name}: {col_type}{is_pk}{is_notnull}')
        
        print()
        print('✅ Migration terminée avec succès!')
        
    else:
        print('❌ Erreur: la table n\'a pas pu être créée')
        sys.exit(1)
    
    db.close()
    
except Exception as e:
    print(f'❌ Erreur lors de la migration: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_MIGRATION

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                  ✅ MIGRATION RÉUSSIE                         ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "La base de données est maintenant prête pour le cache de doublons."
    echo ""
    echo "Vous pouvez maintenant:"
    echo "  - Lancer le dashboard: ./scripts/start_dashboard.sh"
    echo "  - Utiliser la détection de doublons avec cache automatique"
    echo ""
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                  ❌ MIGRATION ÉCHOUÉE                         ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    exit 1
fi
