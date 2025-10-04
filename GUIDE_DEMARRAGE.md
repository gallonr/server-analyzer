# 🚀 Guide de Démarrage - Server Analyzer

**Projet** : Système d'analyse et de visualisation de l'arborescence serveur 28 To  
**Version** : 1.0  
**Date** : 4 octobre 2025  
**Statut** : ✅ Production Ready (Phases 0 à 3 complètes)

---

## 📋 Table des matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Installation](#-installation)
3. [Configuration](#-configuration)
4. [Déploiement serveur](#-déploiement-serveur)
5. [Utilisation](#-utilisation)
6. [Dashboard](#-dashboard)
7. [Exports et comparaisons](#-exports-et-comparaisons)
8. [Résolution de problèmes](#-résolution-de-problèmes)

---

## 🎯 Vue d'ensemble

### Capacités du système

Le Server Analyzer est un programme Python performant capable de :

- ✅ Scanner et analyser **10-20 millions de fichiers** (28 To)
- ✅ Extraire les métadonnées complètes (permissions, propriétaires, dates, tailles)
- ✅ Stocker de manière optimisée dans SQLite avec indexation
- ✅ Scan parallélisé avec **80 workers** sur serveur de calcul
- ✅ Visualisation interactive avec dashboard Streamlit
- ✅ Exploration arborescence avec navigation drill-down
- ✅ Filtres dynamiques (taille, extension, propriétaire, date, nom)
- ✅ Exports multi-formats (CSV, Excel, JSON)
- ✅ Comparaison entre scans successifs
- ✅ Détection d'anomalies (gros fichiers, fichiers anciens, doublons)

### Phases réalisées

- ✅ **Phase 0** : Structure projet et environnement (2h)
- ✅ **Phase 1** : Scanner core et stockage (2h)
- ✅ **Phase 2** : Statistiques et analyses (1h)
- ✅ **Phase 3.1** : Dashboard - Vue d'ensemble (1 jour)
- ✅ **Phase 3.2** : Dashboard - Explorateur et filtres (1 jour)
- ✅ **Phase 3.3** : Dashboard - Comparaisons et exports (1 jour)

### Serveur de production

**Serveur distant** : `user@domaine`  
**Caractéristiques** : 20-80 cœurs CPU, 16-32 Go RAM, Python 3.12

---

## 📦 Installation

### Pré-requis

- Python 3.10 ou supérieur
- 16-32 Go RAM
- Accès SSH au serveur (pour déploiement distant)

### Installation locale (développement/tests)

```bash
# 1. Cloner/télécharger le projet
cd /chemin/vers/server-analyzer

# 2. Créer environnement virtuel
python3 -m venv venv

# 3. Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# 4. Mettre à jour pip
pip install --upgrade pip setuptools wheel

# 5. Installer les dépendances
pip install -r requirements.txt

# 6. Vérifier l'installation
python -c "import pandas, streamlit, plotly; print('✅ Installation OK')"
```

### Installation sur le serveur

Voir section [Déploiement serveur](#-déploiement-serveur)

---

## ⚙️ Configuration

### Fichier config.yaml

Le fichier `config.yaml` contrôle tous les aspects du scan :

```bash
# 1. Copier l'exemple (première fois)
cp config.yaml.example config.yaml

# 2. Éditer la configuration
nano config.yaml
```

### Structure de config.yaml

```yaml
# Chemins racine à scanner
root_paths:
  - "/data/archives"
  - "/home/shared"

# Exclusions
exclusions:
  directories:
    - ".git"
    - "__pycache__"
    - "venv"
  extensions:
    - ".tmp"
    - ".cache"

# Performance
performance:
  num_workers: 80          # Nombre de processus parallèles
  batch_size: 50000        # Taille des lots d'insertion
  queue_size: 1000         # Taille de la queue
  checkpoint_interval: 100000  # Sauvegarde tous les N fichiers

# Base de données
database:
  path: "data/server_analysis.db"
  
# Statistiques
stats:
  large_file_threshold_gb: 10    # Seuil fichier volumineux
  old_file_threshold_days: 730   # Seuil fichier ancien (2 ans)
  enable_duplicate_detection: true
```

### Valider la configuration

```bash
source venv/bin/activate
python src/config_validator.py
```

**Sortie attendue** :
```
✅ Configuration valide
📋 Chemins à scanner: 2
🚫 Exclusions: 5 dossiers, 2 extensions
⚙️  Workers: 80, Batch: 50000
```

---

## 🌐 Déploiement serveur

### Méthode automatique (recommandée)

Le script `deploy.sh` automatise le déploiement complet :

```bash
# Sur votre machine locale
cd /chemin/vers/server-analyzer
./deploy.sh
```

**Ce que fait le script** :
1. ✅ Vérifie la connexion SSH
2. ✅ Crée le répertoire distant `~/server-analyzer`
3. ✅ Synchronise tous les fichiers (exclut venv, cache, data)
4. ✅ Installe `python3-venv` si nécessaire (avec sudo)
5. ✅ Crée l'environnement virtuel distant
6. ✅ Installe toutes les dépendances Python
7. ✅ Crée la structure de dossiers (data, logs, checkpoints)
8. ✅ Copie `config.yaml.example` → `config.yaml`

### ⚠️ Important : Environnement virtuel

Sur les systèmes Debian/Ubuntu récents (Python 3.12+), **vous DEVEZ utiliser un environnement virtuel** pour installer des packages Python.

**❌ NE PAS FAIRE** :
```bash
# Ceci échouera avec "externally-managed-environment"
pip install streamlit
```

**✅ FAIRE** :
```bash
# Toujours activer le venv d'abord
cd ~/server-analyzer
source venv/bin/activate
# Maintenant vous pouvez utiliser pip
pip install <package>
```

### Configuration post-déploiement

```bash
# 1. Se connecter au serveur
ssh user@domaine

# 2. Aller dans le dossier
cd ~/server-analyzer

# 3. Activer l'environnement virtuel
source venv/bin/activate

# 4. Éditer la configuration pour le serveur
nano config.yaml

# 5. Adapter les chemins (exemple pour serveur 28 To)
# root_paths:
#   - "/data/archives"
#   - "/data/projects"

# 6. Tester la configuration
python src/config_validator.py
```

### Scripts utilitaires

```bash
# Connexion SSH rapide
./connect.sh

# Activer l'environnement virtuel (local ou distant)
source activate.sh
# ou
./activate.sh
```

---

## 🔍 Utilisation

### 1. Lancer un scan complet

```bash
# Sur le serveur (après connexion SSH)
cd ~/server-analyzer
source venv/bin/activate

# Lancer le scan (utilise config.yaml)
python scripts/run_scan.py

# Ou avec configuration personnalisée
python scripts/run_scan.py --config config_production.yaml
```

**Exemple de sortie** :
```
🚀 Scan démarré
📂 Chemins : /data/archives, /data/projects
⚙️  Workers : 80
💾 Base de données : data/server_analysis.db

Progression: 100%|████████████████| 4,523,891/4,523,891 [12:34<00:00, 6000 files/s]

✅ Scan terminé avec succès!
📊 Résultats: 4,523,891 fichiers, 12.5 TB
💾 Base de données: data/server_analysis.db
⏱️  Durée: 12m 34s
🚀 Débit: 6,000 fichiers/seconde

📊 Calcul des statistiques...
✅ Statistiques calculées
```

### 2. Test local (développement)

```bash
# Sur votre machine locale
source venv/bin/activate

# Utiliser la configuration de test
python scripts/run_scan.py --config config_test_local.yaml
```

### 3. Options du scanner

```bash
# Voir toutes les options
python scripts/run_scan.py --help

# Options principales :
--config CONFIG    # Fichier de configuration (défaut: config.yaml)
--skip-stats       # Ne pas calculer les statistiques après le scan
--resume           # Reprendre un scan interrompu (checkpoint)
```

### 4. Gestion des scans longs

Pour les scans très longs (plusieurs heures), utilisez `screen` ou `tmux` :

```bash
# Créer une session screen
screen -S scan_serveur

# Lancer le scan
cd ~/server-analyzer
source venv/bin/activate
python scripts/run_scan.py

# Détacher la session : Ctrl+A puis D
# Vous pouvez vous déconnecter, le scan continue

# Revenir à la session plus tard
screen -r scan_serveur
```

---

## 📊 Dashboard

### Lancer le dashboard

```bash
# Sur le serveur (ou en local)
cd ~/server-analyzer
source venv/bin/activate

# Méthode 1 : Script automatique
./scripts/start_dashboard.sh

# Méthode 2 : Commande directe
streamlit run src/dashboard/app.py
```

**URL** : `http://localhost:8501` (local)

### Accès distant au dashboard

Si le dashboard tourne sur le serveur, créez un tunnel SSH :

```bash
# Sur votre machine locale
ssh -L 8501:localhost:8501 user@domaine

# Puis ouvrir dans votre navigateur
# http://localhost:8501
```

### Pages du dashboard

Le dashboard contient 4 pages principales :

#### 1. 🏠 Vue d'ensemble

**Métriques principales** (4 cards) :
- Total fichiers scannés
- Taille totale du serveur
- Nombre de dossiers
- Durée du dernier scan

**Graphiques standards** :
- 📊 Top 10 extensions (bar chart)
- 👤 Top 10 propriétaires (bar chart)
- 📏 Distribution des tailles (histogram)

**Graphiques avancés** :
- 🥧 Pie chart répartition par extension
- 🌳 Treemap volumes hiérarchiques
- 📅 Timeline distribution temporelle

#### 2. 📁 Explorateur

**Navigation arborescence** :
- Sélection dossier racine
- Navigation drill-down (clic sur sous-dossier)
- Bouton "Dossier parent" (remontée)
- Breadcrumb (chemin complet)
- Stats dossier courant (fichiers, taille, top extensions)

**Tableau fichiers** :
- Colonnes : Nom, Taille, Propriétaire, Groupe, Date, Permissions, Extension
- Tri par taille décroissant
- Pagination (50/100/500/1000 fichiers par page)
- Export CSV (page courante ou complet)

**Filtres dynamiques (sidebar)** :
- 💾 **Taille** : Plage min/max (MB)
- 📄 **Extension** : Sélection multiple
- 👤 **Propriétaire** : Sélection multiple
- 📅 **Date modification** : Plage de dates
- 🔤 **Nom fichier** : Pattern de recherche

Boutons :
- ✅ Appliquer (applique filtres et recharge)
- 🔄 Réinitialiser (supprime tous filtres)

#### 3. 📤 Exports

**3 formats d'export disponibles** :

1. **CSV** : Format universel, léger
   - Une ligne par fichier
   - Toutes les métadonnées

2. **Excel** : Format professionnel avec formatage
   - Feuille "Informations" : métadonnées du scan
   - Feuille "Fichiers" : liste complète avec mise en forme
   - Feuille "Extensions" : statistiques par extension
   - Formatage automatique (tailles, dates, couleurs)

3. **JSON** : Format structuré pour traitement programmatique
   - Métadonnées scan
   - Liste fichiers
   - Stats par extension

**Options** :
- ✅ Appliquer les filtres actifs (exporte seulement les fichiers filtrés)
- Bouton téléchargement direct

#### 4. 🔄 Comparaisons

**Comparer 2 scans** :
- Sélection de 2 scans dans la base
- Validation automatique (scans différents)

**Métriques d'évolution** :
- Δ Nombre de fichiers
- Δ Volume total
- Pourcentages d'évolution

**Graphiques** :
- 📈 Évolution (double axe : nb fichiers + volume)
- 🥧 Pie chart catégories de changements

**Détails par catégorie (3 tabs)** :
- ✅ **Nouveaux fichiers** : fichiers ajoutés
- ❌ **Fichiers supprimés** : fichiers retirés
- 🔄 **Fichiers modifiés** : fichiers dont taille/date a changé

Chaque tab :
- Tableau paginé avec détails
- Export CSV de la catégorie

---

## 📁 Exports et comparaisons

### Export CLI (sans dashboard)

Le script `export_results.py` permet d'exporter en ligne de commande :

```bash
source venv/bin/activate

# Lister les scans disponibles
python scripts/export_results.py --list

# Exporter en CSV
python scripts/export_results.py --scan-id 1 --format csv

# Exporter en Excel
python scripts/export_results.py --scan-id 1 --format excel

# Exporter en JSON
python scripts/export_results.py --scan-id 1 --format json

# Spécifier le fichier de sortie
python scripts/export_results.py --scan-id 1 --format csv --output mon_export.csv
```

**Sortie par défaut** : `data/exports/scan_<id>_<timestamp>.<format>`

### Comparaison CLI

Le script `compare_scans.py` permet de comparer 2 scans :

```bash
source venv/bin/activate

# Comparer scan 1 et scan 2
python scripts/compare_scans.py 1 2

# Avec export CSV des différences
python scripts/compare_scans.py 1 2 --export
```

**Sortie** :
```
🔄 Comparaison des scans

Scan 1 : 2025-10-01 14:23:45 (1,234,567 fichiers)
Scan 2 : 2025-10-04 09:15:32 (1,256,789 fichiers)

📊 Résultats :
  ✅ Nouveaux      : 25,000 fichiers (+1.2 TB)
  ❌ Supprimés     : 2,778 fichiers (-0.3 TB)
  🔄 Modifiés      : 15,432 fichiers
  
Fichiers exportés :
  - data/exports/new_files.csv
  - data/exports/deleted_files.csv
  - data/exports/modified_files.csv
```

---

## 🧪 Tests

### Exécuter tous les tests

```bash
source venv/bin/activate

# Tous les tests avec couverture
pytest tests/ -v --cov=src

# Tests spécifiques
pytest tests/test_scanner.py -v
pytest tests/test_database.py -v
pytest tests/test_stats.py -v
pytest tests/test_integration.py -v
```

### Tests de performance

```bash
# Test performance scanner
pytest tests/test_performance.py -v

# Test avec profiling
pytest tests/test_performance.py -v --profile
```

**Résultats attendus** :
```
Tests totaux : 70/70 ✅
Couverture   : 76%
Durée        : ~10 secondes
```

---

## 🐛 Résolution de problèmes

### Erreur : externally-managed-environment

**Symptôme** :
```
error: externally-managed-environment
× This environment is externally managed
```

**Cause** : Installation pip en dehors d'un environnement virtuel sur Debian/Ubuntu

**Solution** :
```bash
# TOUJOURS activer le venv d'abord
cd ~/server-analyzer
source venv/bin/activate
# Puis installer
pip install <package>
```

### Erreur : python3-venv non installé

**Symptôme** :
```
The virtual environment was not created successfully because ensurepip is not available.
```

**Solution** :
```bash
# Installer python3-venv
sudo apt update
sudo apt install python3-venv python3-full

# Puis recréer le venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dashboard ne se lance pas

**Symptôme** :
```
ModuleNotFoundError: No module named 'streamlit'
```

**Cause** : venv non activé ou dépendances non installées

**Solution** :
```bash
cd ~/server-analyzer
source venv/bin/activate
pip install -r requirements.txt
streamlit run src/dashboard/app.py
```

### Scan très lent

**Symptôme** : Débit < 1000 fichiers/seconde

**Solutions** :
1. Augmenter le nombre de workers dans `config.yaml` :
   ```yaml
   performance:
     num_workers: 80  # Adapter au nombre de cœurs
   ```

2. Exclure les dossiers inutiles :
   ```yaml
   exclusions:
     directories:
       - ".git"
       - "__pycache__"
       - "node_modules"
       - ".cache"
   ```

3. Utiliser un SSD pour la base de données

### Base de données corrompue

**Symptôme** :
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution** :
```bash
# Sauvegarder l'ancienne base
mv data/server_analysis.db data/server_analysis.db.backup

# Relancer un scan complet
python scripts/run_scan.py
```

### Scan interrompu

**Symptôme** : Scan arrêté (Ctrl+C, connexion perdue, etc.)

**Solution** :
```bash
# Le scan reprendra automatiquement au dernier checkpoint
python scripts/run_scan.py --resume
```

### Problème de connexion SSH

**Symptôme** :
```
ssh: connect to host 192.168.1.158 port 22: Connection refused
```

**Solutions** :
1. Vérifier la connexion réseau
2. Vérifier que le serveur est accessible
3. Consulter `SSH_GUIDE.md` pour configurer les clés SSH

---

## 📚 Documentation complémentaire

- **README.md** : Vue d'ensemble générale
- **SSH_GUIDE.md** : Configuration SSH et connexion serveur
- **SERVEUR_CONFIG.md** : Configuration spécifique serveur
- **DASHBOARD_QUICKSTART.md** : Guide rapide dashboard
- **PHASE*_RAPPORT.md** : Rapports techniques détaillés par phase

---

## 🎯 Workflow complet recommandé

### Première utilisation

1. **Installation locale (test)** :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python scripts/run_scan.py --config config_test_local.yaml
   ./scripts/start_dashboard.sh
   ```

2. **Déploiement serveur** :
   ```bash
   ./deploy.sh
   ssh user@domaine
   cd ~/server-analyzer
   source venv/bin/activate
   nano config.yaml  # Configurer les chemins
   ```

3. **Premier scan serveur** :
   ```bash
   screen -S scan
   python scripts/run_scan.py
   # Ctrl+A D (détacher)
   ```

4. **Visualisation** :
   ```bash
   # Tunnel SSH depuis votre machine locale
   ssh -L 8501:localhost:8501 user@domaine
   
   # Sur le serveur
   ./scripts/start_dashboard.sh
   
   # Navigateur local : http://localhost:8501
   ```

### Scans réguliers (monitoring)

1. **Planifier un scan hebdomadaire** (cron) :
   ```bash
   # Éditer crontab
   crontab -e
   
   # Ajouter (tous les lundis à 2h du matin)
   0 2 * * 1 /home/rgallon/server-analyzer/venv/bin/python /home/rgallon/server-analyzer/scripts/run_scan.py
   ```

2. **Comparer les scans** :
   ```bash
   # Via dashboard : Page "Comparaisons"
   # Ou CLI :
   python scripts/compare_scans.py <old_scan_id> <new_scan_id> --export
   ```

3. **Exporter les résultats** :
   ```bash
   # Via dashboard : Page "Exports"
   # Ou CLI :
   python scripts/export_results.py --scan-id <id> --format excel
   ```

---

## 📞 Support

Pour toute question ou problème :

1. Consulter ce guide
2. Consulter les rapports de phase (PHASE*_RAPPORT.md)
3. Vérifier les logs : `logs/scan_*.log`
4. Tester la configuration : `python src/config_validator.py`

---

**Bon scan ! 🚀**
