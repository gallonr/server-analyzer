# SERVER ANALYZER

![Production](https://img.shields.io/badge/Status-Production-success?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-1.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Version** : 1.0  
**Date** : Octobre 2025  
**Statut** : Production Ready

---

## 📋 Table des Matières

1. [Description Générale](#-description-générale)
2. [Guide d'Installation](#-guide-dinstallation)
3. [Configuration](#-configuration)
4. [Démarrage de l'Application](#-démarrage-de-lapplication)
5. [Interface de Visualisation](#-interface-de-visualisation)
6. [Utilisation Avancée](#-utilisation-avancée)
7. [Résolution de Problèmes](#-résolution-de-problèmes)
8. [Référence Technique](#-référence-technique)

---

## 🎯 Description Générale

### Vue d'ensemble

**Server Analyzer** est un système complet d'analyse et de visualisation de l'arborescence d'un serveur de fichiers. Il permet de scanner, analyser et visualiser l'organisation de millions de fichiers sur des systèmes de grande capacité (jusqu'à 28 To).

### Fonctionnalités principales

#### 1. Scanner haute performance
- **Scan parallélisé** : Utilise jusqu'à 80 processus simultanés
- **Débit élevé** : ~6,000 fichiers/seconde
- **Robustesse** : Gestion des erreurs et checkpoints automatiques
- **Mémorisation** : Sauvegarde régulière de la progression

#### 2. Base de données SQLite optimisée
- **Stockage efficace** : Mode WAL pour performances optimales
- **Indexation** : Indexes sur tous les champs clés
- **Statistiques agrégées** : Calculs pré-calculés pour accès rapide
- **Multi-scans** : Conservation de l'historique des analyses

#### 3. Dashboard interactif Streamlit
- **4 pages spécialisées** :
  - Vue d'ensemble (statistiques globales)
  - Explorateur (navigation arborescence)
  - Comparaisons (évolution entre scans)
  - Exports (téléchargements de données)
- **Visualisations riches** : 10+ types de graphiques Plotly
- **Filtres dynamiques** : Par taille, date, extension, propriétaire
- **Performance** : Cache intelligent, requêtes optimisées

#### 4. Détection de doublons
- **Identification** : Basée sur hash SHA-256
- **Performance** : Traitement parallélisé
- **Filtrage** : Par propriétaire, taille, nombre de copies
- **Export** : Résultats filtrables et exportables

#### 5. Outils d'export et comparaison
- **Formats multiples** : CSV, Excel, JSON
- **Comparaisons** : Différentiels entre 2 scans
- **CLI et GUI** : Scripts en ligne de commande + interface web

### Architecture technique

```
┌─────────────────────────────────────────────────────────┐
│                   Serveur de Fichiers                    │
│                      (~28 To)                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Scanner Parallèle    │
        │  (60-80 workers)       │
        │  • multiprocessing     │
        │  • os.scandir()        │
        │  • Checkpointing       │
        └────────┬───────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │   Base SQLite (WAL)     │
        │  • files (données)      │
        │  • directory_stats      │
        │  • scans (historique)   │
        │  • duplicates (hash)    │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  Dashboard Streamlit    │
        │  • Vue d'ensemble       │
        │  • Explorateur          │
        │  • Comparaisons         │
        │  • Exports              │
        └─────────────────────────┘
```

### Cas d'usage

1. **Audit de stockage**
   - Identifier les gros consommateurs d'espace
   - Détecter les fichiers anciens non utilisés
   - Trouver les doublons

2. **Optimisation**
   - Planifier le nettoyage de données
   - Identifier les opportunités de compression
   - Optimiser la structure de dossiers

3. **Conformité**
   - Suivre l'évolution du stockage
   - Générer des rapports pour la direction
   - Documenter l'organisation des données

4. **Migration**
   - Comparer avant/après migration
   - Valider l'intégrité des transferts
   - Planifier les ressources nécessaires

---

## 📦 Guide d'Installation

### Prérequis système

#### Matériel minimum
- **CPU** : 4 cœurs (8+ recommandés pour scan)
- **RAM** : 16 Go (32 Go recommandés)
- **Disque** : 10 Go d'espace libre (pour base de données + logs)
- **Réseau** : Accès au serveur de fichiers à scanner

#### Logiciels requis
- **OS** : Linux (Debian/Ubuntu recommandé), macOS, ou Windows
- **Python** : Version 3.10 ou supérieure
- **pip** : Gestionnaire de paquets Python
- **SSH** : Pour déploiement distant (optionnel)

### Installation locale (développement/tests)

#### 1. Télécharger le projet

```bash
# Option A : Cloner depuis Git
git clone <URL_DU_REPO>
cd server-analyzer

# Option B : Extraire l'archive
tar -xzf server-analyzer.tar.gz
cd server-analyzer
```

#### 2. Créer un environnement virtuel Python

```bash
# Créer l'environnement
python3 -m venv venv

# Activer l'environnement
# Sur Linux/macOS :
source venv/bin/activate

# Sur Windows :
venv\Scripts\activate
```

**Vérification** : Le prompt doit afficher `(venv)`.

#### 3. Mettre à jour pip

```bash
pip install --upgrade pip setuptools wheel
```

#### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Paquets installés** :
- `streamlit>=1.28.0` : Framework dashboard
- `plotly>=5.17.0` : Graphiques interactifs
- `pandas>=2.0.0` : Manipulation de données
- `pyyaml>=6.0` : Configuration YAML
- `tqdm>=4.66.0` : Barres de progression
- `pytest>=7.4.0` : Tests unitaires

#### 5. Vérifier l'installation

```bash
python -c "import streamlit, plotly, pandas; print('✅ Installation réussie !')"
```

#### 6. Créer les dossiers de données

```bash
mkdir -p data/checkpoints data/exports logs
```

### Installation sur serveur distant

#### 1. Préparer le serveur

```bash
# Se connecter au serveur
ssh utilisateur@serveur.domaine.fr

# Vérifier Python
python3 --version  # Doit être >= 3.10

# Créer dossier projet
mkdir -p ~/server-analyzer
```

#### 2. Déployer les fichiers

**Option A : Script automatique (recommandé)**

```bash
# Sur votre machine locale
./deploy.sh
```

Ce script :
- Synchronise les fichiers via rsync
- Crée l'environnement virtuel
- Installe les dépendances
- Configure les permissions

**Option B : Transfert manuel**

```bash
# Depuis votre machine locale
rsync -avz --exclude 'venv' --exclude '*.pyc' \
  ./ utilisateur@serveur:/home/utilisateur/server-analyzer/

# Sur le serveur
cd ~/server-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configuration SSH (optionnel mais recommandé)

Créer `~/.ssh/config` sur votre machine locale :

```
Host serveurAnalyse
    HostName A DEFINIR
    User user
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Utilisation simplifiée :
```bash
ssh serveurAnalyse
```

Plus de détails dans [`SSH_GUIDE.md`](SSH_GUIDE.md).

---

## ⚙️ Configuration

### Fichier config.yaml

Le fichier [`config.yaml`](config.yaml) centralise toute la configuration. Un exemple est fourni dans [`config.yaml.example`](config.yaml.example).

#### Structure complète

```yaml
# Chemins racine à scanner
root_paths:
  - "/data/archives"
  - "/data/projects"
  - "/home/shared"

# Exclusions
exclusions:
  directories:
    - ".git"
    - "__pycache__"
    - "venv"
    - "node_modules"
    - ".cache"
  extensions:
    - ".tmp"
    - ".cache"
    - ".swp"
    - ".bak"

# Performance
performance:
  num_workers: 80              # Processus parallèles
  batch_size: 50000            # Taille lots d'insertion
  queue_size: 1000             # Taille queue multiprocessing
  checkpoint_interval: 100000  # Sauvegarde tous les N fichiers

# Base de données
database:
  path: "data/server_analysis.db"
  pragma:
    journal_mode: "WAL"
    synchronous: "NORMAL"
    cache_size: -64000         # 64 Mo
    temp_store: "MEMORY"

# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/server_analyzer.log"
  max_bytes: 10485760          # 10 Mo
  backup_count: 5

# Dashboard
dashboard:
  port: 8501
  host: "0.0.0.0"
  title: "Server Analysis Dashboard"
  cache_ttl: 300               # 5 minutes

# Statistiques
stats:
  large_file_threshold_gb: 10
  old_file_days: 730           # 2 ans

# Détection doublons
duplicates:
  min_size_bytes: 1024         # 1 KB minimum
  hash_algorithm: "sha256"
  num_workers: 60
  enable_cache: true

# Avancé
advanced:
  enable_profiling: false
  profiling_output: "logs/profiling.prof"
```

#### Paramètres clés

| Paramètre | Description | Recommandation |
|-----------|-------------|----------------|
| `root_paths` | Chemins à scanner | Chemins absolus |
| `num_workers` | Parallélisme | 60-80 (selon CPU) |
| `batch_size` | Taille lots DB | 50000 par défaut |
| `checkpoint_interval` | Fréquence sauvegarde | 100000 fichiers |
| `journal_mode: WAL` | Mode SQLite | Toujours WAL |
| `large_file_threshold_gb` | Seuil "gros fichier" | 10 Go par défaut |

#### Validation de la configuration

```bash
python src/config_validator.py
```

Affiche :
- ✅ Configuration valide
- ⚠️ Avertissements (chemins inexistants, etc.)
- ❌ Erreurs critiques

---

## 🚀 Démarrage de l'Application

### Workflow complet

```
1. Configuration → 2. Scan → 3. Analyse → 4. Visualisation
```

### 1. Premier scan

#### Scan local (test)

```bash
# Activer environnement
source venv/bin/activate

# Lancer scan avec configuration par défaut
python scripts/run_scan.py

# Ou avec config personnalisée
python scripts/run_scan.py --config config_test.yaml
```

#### Scan serveur (production)

```bash
# Se connecter au serveur
ssh utilisateur@serveur

# Naviguer vers le projet
cd ~/server-analyzer
source venv/bin/activate

# Lancer en arrière-plan avec screen
screen -S scan
python scripts/run_scan.py
# Ctrl+A puis D pour détacher

# Surveiller la progression
screen -r scan
```

**Options du scanner** :

```bash
python scripts/run_scan.py --help

Options:
  --config PATH       Fichier de configuration (défaut: config.yaml)
  --skip-stats        Ne pas calculer les statistiques
  --resume            Reprendre un scan interrompu
  --dry-run           Simulation sans écriture
```

#### Sortie attendue

```
🚀 Scan démarré
📂 Chemins : /data/archives, /data/projects
⚙️  Workers : 80
💾 Base de données : data/server_analysis.db

Progression: 100%|██████████| 4,523,891/4,523,891 [12:34<00:00, 6000 files/s]

✅ Scan terminé avec succès!
📊 Résultats:
   • Fichiers scannés : 4,523,891
   • Volume total : 12.5 TB
   • Durée : 12m 34s
   • Débit : 6,000 fichiers/s

📈 Calcul des statistiques...
✅ Statistiques calculées
```

### 2. Lancer le dashboard

#### Méthode 1 : Script automatique (recommandé)

```bash
./scripts/start_dashboard.sh
```

Le script :
1. Vérifie l'environnement virtuel
2. Vérifie les dépendances
3. Vérifie la base de données
4. Lance Streamlit

#### Méthode 2 : Commande manuelle

```bash
source venv/bin/activate
streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

#### Accès au dashboard

**Local** : [http://localhost:8501](http://localhost:8501)

**Distant** (tunnel SSH) :
```bash
# Sur votre machine locale
ssh -L 8501:localhost:8501 utilisateur@serveur

# Puis ouvrir dans le navigateur
http://localhost:8501
```

### 3. Arrêter l'application

```bash
# Arrêter le dashboard
Ctrl+C dans le terminal

# Arrêter un scan en cours
Ctrl+C (crée un checkpoint automatique)

# Détacher une session screen
Ctrl+A puis D

# Réattacher une session screen
screen -r scan
```

---

## 🎨 Interface de Visualisation

### Navigation générale

Le dashboard Streamlit comprend :
- **Sidebar gauche** : Navigation et sélection du scan
- **Zone principale** : Contenu de la page active
- **Footer** : Version et informations

### Sélection du scan

En haut de la sidebar :

```
📊 Sélectionner un scan
─────────────────────────────
▼ 2025-10-04 14:30:45 (Terminé)
  └─ 4.5M fichiers | 12.5 TB
```

- Affiche tous les scans disponibles
- Indique le statut (Terminé, En cours, Erreur)
- Montre le résumé (nombre de fichiers, volume)

### Page 1 : 🏠 Vue d'ensemble

#### Métriques principales

4 cartes en haut de page :

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 📄 Fichiers  │ 💾 Volume    │ 📁 Dossiers  │ ⏱️ Durée     │
│  4,523,891   │   12.5 TB    │    125,432   │   12m 34s    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

#### Graphiques standards

**1. Top 10 Extensions (Bar Chart)**

```
Extensions         Taille
─────────────────────────────────────
.mp4          ████████████  3.2 TB
.mkv          ██████████    2.8 TB
.pdf          ████          1.1 TB
.jpg          ███           0.9 TB
...
```

- Barre horizontale
- Tooltip au survol : nombre de fichiers + taille
- Interactif (clic pour filtrer)

**2. Top 10 Propriétaires (Bar Chart)**

```
Propriétaire      Taille
─────────────────────────────────────
user1         ████████████  4.5 TB
user2         ██████████    3.2 TB
shared        ████          1.8 TB
...
```

**3. Distribution des Tailles (Histogram)**

```
Nombre de fichiers
      │
  1M  │     █
      │    ███
 500k │   █████
      │  ███████
      │ █████████
      └────────────────
       <1MB  1-100MB  >1GB
```

- Logarithmique pour visualiser tous les ordres de grandeur
- Catégories : < 1 KB, 1 KB-1 MB, 1-10 MB, 10-100 MB, 100 MB-1 GB, > 1 GB

#### Visualisations avancées (onglets)

**Onglet 1 : Répartition (Pie Chart)**

```
        .mp4 (25.6%)
     ╱            ╲
  .mkv            .pdf
 (22.4%)         (8.8%)
     ╲            ╱
      ╲          ╱
       .jpg (autres)
```

- Montre la proportion de chaque extension
- Top 10 extensions + "Autres"
- Couleurs distinctes
- Pourcentages sur les segments

**Onglet 2 : Hiérarchie (Treemap)**

```
┌─────────────────────────────────────────────┐
│ /data/archives (7.2 TB)                     │
├───────────────────────┬─────────────────────┤
│ /videos              │ /documents          │
│  5.1 TB              │  2.1 TB             │
│ ┌─────┬──────┐      │ ┌─────┬──────┐     │
│ │.mp4 │.mkv  │      │ │.pdf │.docx │     │
│ │3.2T │1.9T  │      │ │1.8T │0.3T  │     │
│ └─────┴──────┘      │ └─────┴──────┘     │
└───────────────────────┴─────────────────────┘
```

- Visualise la hiérarchie des dossiers
- Taille proportionnelle au volume
- Drill-down : clic pour descendre dans l'arborescence
- Couleurs par niveau

**Onglet 3 : Temporel (Timeline)**

```
Nb fichiers          Taille cumulée
    │                      │
 1M │                  15TB│
    │    █                 │         ████
500k│   ███            10TB│      ███████
    │  █████            5TB│   ████████
    │ ███████              │ ███████
    └──────────────         └──────────────
     2020  2021  2022       2020  2021  2022
```

- Double axe Y (nombre + taille)
- Distribution par année de modification
- Identifie les périodes d'activité
- Détecte les fichiers anciens

#### Bouton Rafraîchir

```
[🔄 Rafraîchir les données]
```

- Actualise le cache
- Recharge les statistiques
- Utile après un nouveau scan

### Page 2 : 📁 Explorateur

#### Navigation arborescence

```
📂 Dossier actuel : /data/archives/videos

┌─ Sous-dossiers ──────────────────────────────┐
│ 📁 documentaires/    1,234 fichiers  2.3 TB  │
│ 📁 series/           5,678 fichiers  4.1 TB  │
│ 📁 films/            2,345 fichiers  3.2 TB  │
└──────────────────────────────────────────────┘
```

**Navigation** :
- Clic sur un dossier pour y entrer
- Breadcrumb en haut pour remonter
- Statistiques pour chaque dossier

#### Statistiques du dossier actuel

```
┌──────────────┬──────────────┬──────────────┐
│ 📄 Fichiers  │ 💾 Taille    │ 📊 Moyenne   │
│    9,257     │   9.6 TB     │   1.04 GB    │
└──────────────┴──────────────┴──────────────┘
```

#### Tableau des fichiers

```
Nom                    Taille      Modifié         Propriétaire
──────────────────────────────────────────────────────────────
film1.mkv             2.3 GB   2024-03-15      user1
documentaire.mp4      1.8 GB   2024-02-10      user2
serie_s01e01.mkv      850 MB   2023-12-05      shared
...

[← Précédent]  Page 1/234  [Suivant →]
```

- Pagination : 100 fichiers par page
- Tri : clic sur colonne pour trier
- Recherche : barre de recherche intégrée

#### Filtres (sidebar)

```
🔍 Filtres

▼ Taille
  ○ Toutes tailles
  ● Personnalisé
    Min : [___] MB
    Max : [___] GB

▼ Date de modification
  ☑ Derniers 7 jours
  ☐ Dernier mois
  ☐ Dernière année
  ● Plage personnalisée
    Du : [____-__-__]
    Au : [____-__-__]

▼ Extensions
  ☑ .mp4
  ☑ .mkv
  ☐ .avi
  [Afficher plus...]

▼ Propriétaires
  ☑ user1
  ☐ user2
  ☐ shared
  [Afficher plus...]

[✅ Appliquer les filtres]
[🔄 Réinitialiser]
```

**Indicateur de résultats** :
```
🔍 123,456 fichiers correspondent (3.2 TB)
```

#### Export de la page

```
[💾 Exporter la page actuelle (CSV)]
[💾 Exporter tous les résultats (CSV)]  (si < 10k)
```

- CSV téléchargeable
- Respecte les filtres actifs

### Page 3 : 🔄 Comparaisons

#### Sélection des scans

```
Comparer deux scans

Scan 1 (ancien)         Scan 2 (récent)
─────────────────────   ─────────────────────
▼ 2025-09-01 10:00     ▼ 2025-10-04 14:30
  4.2M fichiers          4.5M fichiers
  11.8 TB                12.5 TB

[🔄 Comparer]
```

#### Résumé des différences

```
┌────────────────────────────────────────────┐
│ 📊 Résumé de la comparaison                │
├────────────────────────────────────────────┤
│ ➕ Fichiers ajoutés     :  342,567 (+7.5%) │
│ ➖ Fichiers supprimés   :   45,123 (-1.0%) │
│ 🔄 Fichiers modifiés    :   12,890         │
│ 📈 Évolution du volume  :  +700 GB (+5.9%) │
└────────────────────────────────────────────┘
```

#### Graphiques de comparaison

**1. Évolution du volume par extension**

```
Extension    Scan 1    Scan 2    Évolution
────────────────────────────────────────────
.mp4         3.0 TB → 3.2 TB    +200 GB ▲
.mkv         2.8 TB → 2.8 TB      0 GB  ─
.pdf         1.0 TB → 1.1 TB    +100 GB ▲
```

- Bar chart double pour comparaison visuelle
- Flèches indiquant la tendance

**2. Fichiers ajoutés par dossier (Top 10)**

```
Dossier                   Nb fichiers
──────────────────────────────────────
/data/new_project         ████████  45,123
/data/archives/2025       ██████    32,891
/home/user1/downloads     ████      18,456
...
```

**3. Fichiers supprimés par dossier (Top 10)**

Même format que les ajouts.

#### Liste détaillée des changements

```
Type        Fichier                        Taille    Date
─────────────────────────────────────────────────────────
➕ Ajouté   /data/new/file1.mp4           2.3 GB   2025-10-02
➖ Supprimé /data/old/file2.pdf           15 MB    2025-09-15
🔄 Modifié  /home/user1/doc.docx          2.1 MB   2025-10-01
...

[💾 Exporter les différences (CSV)]
```

#### Export différentiel

```
[💾 Télécharger rapport complet (Excel)]
```

Le rapport Excel contient 3 feuilles :
- **Résumé** : Statistiques globales
- **Ajouts** : Liste des fichiers ajoutés
- **Suppressions** : Liste des fichiers supprimés
- **Modifications** : Liste des fichiers modifiés

### Page 4 : 💾 Exports

#### Sélection du scan et format

```
📦 Exporter les données

Scan à exporter
▼ 2025-10-04 14:30:45
  4.5M fichiers | 12.5 TB

Format d'export
○ CSV (virgule)
● CSV (point-virgule)
○ Excel (.xlsx)
○ JSON

☐ Inclure les statistiques agrégées
☑ Inclure les métadonnées de scan

[💾 Générer l'export]
```

#### Exports rapides

```
Exports pré-configurés

[📊 Top 100 fichiers les plus gros]
[📁 Statistiques par dossier]
[👤 Statistiques par propriétaire]
[📈 Résumé extensions]
```

- Téléchargements instantanés
- Formats CSV optimisés

#### Résultats

Après génération :

```
✅ Export généré avec succès !

📄 Fichier : scan_2025-10-04_export.csv
📊 Lignes : 4,523,891
💾 Taille : 523 MB

[⬇️ Télécharger]
```

### Page 5 : 🔗 Doublons (bonus)

#### Configuration de la détection

```
🔍 Détection de doublons

Configuration
─────────────
Taille minimale : [1] KB
Nombre de workers : [Auto] (60)
☑ Activer le cache

[🚀 Lancer la détection]
```

#### Progression

```
Détection en cours...

Étape 1/3 : Calcul des hashs
████████████████████░░  80% (3.6M/4.5M)

Étape 2/3 : Identification des doublons
████████████████████░░  45% (2.0M/4.5M)

Étape 3/3 : Regroupement
██░░░░░░░░░░░░░░░░░░░░  10% (450k/4.5M)
```

#### Résultats

**Statistiques globales** :

```
┌────────────────────────────────────────────┐
│ 📊 Résultats de la détection               │
├────────────────────────────────────────────┤
│ Groupes de doublons  :  12,345             │
│ Fichiers en double   :  87,654 (1.9%)      │
│ Espace récupérable   :  2.3 TB             │
│ Durée de détection   :  3m 45s             │
└────────────────────────────────────────────┘
```

**Filtres** :

```
🔍 Filtrer les doublons

▼ Propriétaires
  ☑ user1 (12,345 doublons)
  ☐ user2 (5,678 doublons)

▼ Nombre de copies
  Min : [2]  Max : [___]

▼ Taille fichier
  Min : [1] KB  Max : [___] GB

▼ Ordre de tri
  ● Espace récupérable (décroissant)
  ○ Nombre de copies
  ○ Taille fichier

[✅ Appliquer]

📊 234 groupes correspondent (1.2 TB récupérables)
```

**Liste des groupes** :

```
┌─ Groupe #1 ─────────────────────────────────────────┐
│ 📄 film_2024.mkv                                    │
│ Taille : 2.3 GB | Copies : 5 | Récupérable : 9.2 GB │
│                                                      │
│ Emplacements:                                        │
│  1. /data/archives/films/film_2024.mkv (user1)      │
│  2. /home/user2/downloads/film_2024.mkv (user2)     │
│  3. /backup/old/film_2024.mkv (shared)              │
│  4. /data/duplicates/film_2024.mkv (user1)          │
│  5. /tmp/film_2024.mkv (user1)                      │
└──────────────────────────────────────────────────────┘

[💾 Exporter ce groupe]
```

#### Exports

```
[💾 Exporter tous les doublons (CSV)]
[💾 Exporter résumé (CSV)]
[📊 Télécharger rapport détaillé (Excel)]
```

---

## 🔧 Utilisation Avancée

### Scripts en ligne de commande

#### 1. Export de résultats

```bash
python scripts/export_results.py --help

Options:
  --list                  Lister les scans disponibles
  --scan-id ID            ID du scan à exporter
  --format {csv,excel,json}  Format de sortie
  --output PATH           Fichier de sortie
  --filter-ext EXT        Filtrer par extension
  --filter-owner OWNER    Filtrer par propriétaire
  --min-size SIZE         Taille minimale
  --max-size SIZE         Taille maximale
```

**Exemples** :

```bash
# Lister les scans
python scripts/export_results.py --list

# Export CSV complet
python scripts/export_results.py \
  --scan-id 1 \
  --format csv \
  --output exports/scan_complet.csv

# Export filtré (fichiers .mp4 > 1 GB)
python scripts/export_results.py \
  --scan-id 1 \
  --format excel \
  --filter-ext .mp4 \
  --min-size 1073741824 \
  --output exports/gros_videos.xlsx
```

#### 2. Comparaison de scans

```bash
python scripts/compare_scans.py --help

Options:
  --scan-id-1 ID        Premier scan (ancien)
  --scan-id-2 ID        Deuxième scan (récent)
  --output PATH         Fichier de sortie
  --format {text,csv,json}  Format du rapport
  --detailed            Inclure détails fichier par fichier
```

**Exemple** :

```bash
python scripts/compare_scans.py \
  --scan-id-1 1 \
  --scan-id-2 2 \
  --format csv \
  --output comparaison.csv \
  --detailed
```

### Utilisation programmatique (API Python)

#### 1. Importer les modules

```python
from database import DatabaseManager
from stats import (
    get_directory_stats,
    get_extension_stats,
    get_owner_stats,
    detect_large_files,
    detect_duplicates
)
from utils import format_size, format_timestamp
```

#### 2. Se connecter à la base

```python
db = DatabaseManager('data/server_analysis.db')
```

#### 3. Récupérer des statistiques

```python
# Statistiques par extension
ext_stats = get_extension_stats(db.conn, scan_id=1)
for ext, count, size in ext_stats:
    print(f"{ext}: {count} fichiers, {format_size(size)}")

# Fichiers volumineux
large_files = detect_large_files(
    db.conn,
    scan_id=1,
    threshold_gb=10
)
for path, size, owner in large_files:
    print(f"{path}: {format_size(size)} ({owner})")
```

#### 4. Requêtes SQL personnalisées

```python
import sqlite3

conn = sqlite3.connect('data/server_analysis.db')
cursor = conn.cursor()

# Fichiers .pdf créés cette année
cursor.execute("""
    SELECT path, size, modified_time
    FROM files
    WHERE scan_id = ?
      AND extension = '.pdf'
      AND modified_time >= strftime('%s', 'now', 'start of year')
    ORDER BY size DESC
    LIMIT 100
""", (1,))

for row in cursor.fetchall():
    print(row)
```

### Automatisation

#### 1. Script cron pour scans réguliers

Créer `scripts/cron_scan.sh` :

```bash
#!/bin/bash
cd /home/utilisateur/server-analyzer
source venv/bin/activate

# Lancer scan
python scripts/run_scan.py >> logs/cron_scan.log 2>&1

# Nettoyer anciens scans (garder 10 derniers)
python scripts/cleanup_old_scans.py --keep 10
```

Ajouter à crontab :

```bash
# Scan tous les lundis à 2h du matin
0 2 * * 1 /home/utilisateur/server-analyzer/scripts/cron_scan.sh
```

#### 2. Notifications par email

Créer `scripts/notify_scan_complete.py` :

```python
import smtplib
from email.mime.text import MIMEText
from database import DatabaseManager
from utils import format_size

db = DatabaseManager('data/server_analysis.db')
scan_info = db.get_latest_scan()

msg = MIMEText(f"""
Scan terminé avec succès !

Fichiers : {scan_info['total_files']:,}
Volume : {format_size(scan_info['total_size_bytes'])}
Durée : {scan_info['duration']} secondes
""")

msg['Subject'] = 'Scan serveur terminé'
msg['From'] = 'scanner@serveur.com'
msg['To'] = 'admin@serveur.com'

smtp = smtplib.SMTP('localhost')
smtp.send_message(msg)
smtp.quit()
```

Intégrer dans `run_scan.py` ou script cron.

---

## 🐛 Résolution de Problèmes

### Problèmes d'installation

#### Erreur : `python3: command not found`

**Cause** : Python non installé ou non dans PATH.

**Solution** :
```bash
# Debian/Ubuntu
sudo apt-get install python3 python3-venv python3-pip

# macOS (avec Homebrew)
brew install python3

# Vérifier
python3 --version
```

#### Erreur : `No module named 'streamlit'`

**Cause** : Dépendances non installées ou environnement virtuel non activé.

**Solution** :
```bash
# Activer environnement
source venv/bin/activate

# Réinstaller dépendances
pip install -r requirements.txt
```

#### Erreur : `Permission denied` lors de l'installation

**Cause** : Tentative d'installation système sans sudo.

**Solution** : Toujours utiliser un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Problèmes de scan

#### Scan très lent (< 1000 fichiers/s)

**Causes possibles** :
1. Trop peu de workers
2. Système de fichiers lent (réseau)
3. Beaucoup de petits fichiers

**Solutions** :
```yaml
# Dans config.yaml
performance:
  num_workers: 80  # Augmenter (tester 100-120)
  batch_size: 100000  # Augmenter si beaucoup de fichiers
```

#### Erreur : `Too many open files`

**Cause** : Limite système dépassée.

**Solution** :
```bash
# Vérifier limite actuelle
ulimit -n

# Augmenter temporairement
ulimit -n 65536

# Augmenter définitivement (ajouter dans /etc/security/limits.conf)
* soft nofile 65536
* hard nofile 65536
```

#### Scan interrompu (Ctrl+C ou crash)

**Solution** : Reprendre avec l'option `--resume` :
```bash
python scripts/run_scan.py --resume
```

Le scan reprend au dernier checkpoint (tous les 100,000 fichiers par défaut).

### Problèmes de base de données

#### Erreur : `database is locked`

**Cause** : Accès concurrent ou crash précédent.

**Solutions** :
1. Vérifier qu'aucun autre processus n'accède à la DB
2. Vérifier mode WAL activé dans `config.yaml`
3. Si problème persiste :
```bash
sqlite3 data/server_analysis.db "PRAGMA integrity_check;"
```

#### Base de données corrompue

**Solution** : Exporter et recréer
```bash
# Exporter données
sqlite3 data/server_analysis.db .dump > backup.sql

# Recréer base
mv data/server_analysis.db data/server_analysis.db.old
sqlite3 data/server_analysis.db < backup.sql
```

#### Taille de base de données excessive

**Cause** : Beaucoup de scans historiques.

**Solution** : Nettoyer anciens scans
```bash
python scripts/cleanup_old_scans.py --keep 5
```

Ou manuellement :
```bash
sqlite3 data/server_analysis.db "VACUUM;"
```

### Problèmes de dashboard

#### Dashboard ne démarre pas

**Vérifications** :
```bash
# 1. Environnement activé ?
which python  # Doit pointer vers venv/bin/python

# 2. Streamlit installé ?
python -c "import streamlit; print(streamlit.__version__)"

# 3. Base de données existe ?
ls -lh data/server_analysis.db

# 4. Port 8501 disponible ?
netstat -tuln | grep 8501
```

#### Erreur : `Base de données introuvable`

**Cause** : Aucun scan effectué.

**Solution** :
```bash
python scripts/run_scan.py
```

#### Erreur : `Aucun scan disponible`

**Cause** : Base existe mais table `scans` vide.

**Solution** : Lancer un scan complet.

#### Dashboard lent / non réactif

**Causes et solutions** :

1. **Cache désactivé** → Vérifier `@st.cache_data` dans le code
2. **Requêtes lentes** → Vérifier indexes SQL :
```bash
sqlite3 data/server_analysis.db
.schema files
-- Doit afficher CREATE INDEX ...
```
3. **Trop de données** → Utiliser filtres et pagination
4. **Ressources limitées** → Augmenter RAM/CPU

#### Port 8501 déjà utilisé

**Solution** : Changer le port
```bash
streamlit run src/dashboard/app.py --server.port 8502
```

### Problèmes de connexion SSH

#### Connexion refusée

**Vérifications** :
```bash
# Serveur SSH actif ?
sudo systemctl status sshd

# Port SSH correct ?
ssh -p 22 utilisateur@serveur

# Firewall bloquant ?
sudo ufw status
```

#### Tunnel SSH se déconnecte

**Solution** : Ajouter keep-alive dans `~/.ssh/config` :
```
ServerAliveInterval 60
ServerAliveCountMax 3
```

#### Permission denied (publickey)

**Solution** : Vérifier clé SSH
```bash
# Générer clé si inexistante
ssh-keygen -t rsa -b 4096

# Copier vers serveur
ssh-copy-id utilisateur@serveur

# Tester
ssh -v utilisateur@serveur
```

### Problèmes de performance

#### Dashboard très lent au chargement

**Optimisations** :

1. **Augmenter cache** dans `.streamlit/config.toml` :
```toml
[server]
maxMessageSize = 500

[runner]
fastReruns = true
```

2. **Paginer les résultats** : Limiter nombre de lignes affichées

3. **Pré-calculer statistiques** : Lancer `run_scan.py` sans `--skip-stats`

#### Requêtes SQL lentes

**Diagnostic** :
```python
# Dans src/dashboard/app.py
cursor.execute("EXPLAIN QUERY PLAN SELECT ...")
print(cursor.fetchall())
```

**Solutions** :
- Vérifier indexes créés
- Utiliser `LIMIT` dans requêtes
- Optimiser les `WHERE` clauses

---

## 📚 Référence Technique

### Structure de la base de données

#### Table `scans`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID unique du scan |
| `start_time` | REAL | Timestamp début (epoch) |
| `end_time` | REAL | Timestamp fin |
| `duration` | REAL | Durée en secondes |
| `status` | TEXT | "running", "completed", "failed" |
| `total_files` | INTEGER | Nombre total de fichiers |
| `total_size_bytes` | INTEGER | Volume total en octets |
| `num_directories` | INTEGER | Nombre de dossiers |
| `config_snapshot` | TEXT | Configuration JSON |

#### Table `files`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID unique |
| `scan_id` | INTEGER | Référence vers `scans.id` |
| `path` | TEXT | Chemin complet |
| `name` | TEXT | Nom du fichier |
| `extension` | TEXT | Extension (avec point) |
| `directory` | TEXT | Dossier parent |
| `size` | INTEGER | Taille en octets |
| `created_time` | REAL | Date création (epoch) |
| `modified_time` | REAL | Date modification (epoch) |
| `accessed_time` | REAL | Dernier accès (epoch) |
| `owner` | TEXT | Propriétaire (UID ou nom) |
| `permissions` | TEXT | Permissions (format octal) |
| `is_symlink` | INTEGER | 1 si lien symbolique |
| `error` | TEXT | Message d'erreur (NULL si OK) |

**Indexes** :
- `idx_files_scan_id` sur `scan_id`
- `idx_files_directory` sur `directory`
- `idx_files_extension` sur `extension`
- `idx_files_owner` sur `owner`
- `idx_files_size` sur `size`

#### Table `directory_stats`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID unique |
| `scan_id` | INTEGER | Référence vers `scans.id` |
| `directory` | TEXT | Chemin du dossier |
| `file_count` | INTEGER | Nombre de fichiers |
| `total_size` | INTEGER | Taille totale |
| `avg_file_size` | REAL | Taille moyenne |
| `max_file_size` | INTEGER | Fichier le plus gros |
| `min_file_size` | INTEGER | Fichier le plus petit |

**Index** : `idx_directory_stats_scan_dir` sur `(scan_id, directory)`

#### Table `duplicates` (optionnelle)

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INTEGER PRIMARY KEY | ID unique |
| `scan_id` | INTEGER | Référence vers `scans.id` |
| `file_hash` | TEXT | Hash SHA-256 du contenu |
| `size` | INTEGER | Taille du fichier |
| `file_paths` | TEXT | JSON array des chemins |
| `file_owners` | TEXT | JSON array des propriétaires |
| `num_copies` | INTEGER | Nombre de copies |
| `wasted_space` | INTEGER | Espace gaspillé |

**Index** : `idx_duplicates_hash` sur `file_hash`

### Schéma de configuration

Voir [`config.yaml.example`](config.yaml.example) pour la configuration complète annotée.

**Validation** : [`src/config_validator.py`](src/config_validator.py)

### Architecture logicielle

#### Modules Python

| Module | Responsabilité | Lignes |
|--------|----------------|--------|
| `src/scanner.py` | Scan parallèle du système de fichiers | ~350 |
| `src/database.py` | Gestion base SQLite + migrations | ~280 |
| `src/stats.py` | Calcul statistiques et agrégations | ~470 |
| `src/utils.py` | Fonctions utilitaires (formatage, etc.) | ~120 |
| `src/config_validator.py` | Validation configuration YAML | ~180 |

#### Dashboard Streamlit

| Fichier | Description | Lignes |
|---------|-------------|--------|
| `src/dashboard/app.py` | Application principale | ~220 |
| `src/dashboard/components/overview.py` | Page vue d'ensemble | ~360 |
| `src/dashboard/components/explorer.py` | Page explorateur | ~500 |
| `src/dashboard/components/filters.py` | Système de filtres | ~330 |
| `src/dashboard/components/charts.py` | Graphiques Plotly | ~250 |
| `src/dashboard/components/comparisons.py` | Page comparaisons | ~280 |
| `src/dashboard/components/exports.py` | Page exports | ~200 |

#### Scripts utilitaires

| Script | Usage | Options |
|--------|-------|---------|
| `scripts/run_scan.py` | Lancer un scan | `--config`, `--resume`, `--skip-stats` |
| `scripts/export_results.py` | Exporter données | `--scan-id`, `--format`, `--filter-*` |
| `scripts/compare_scans.py` | Comparer 2 scans | `--scan-id-1`, `--scan-id-2`, `--detailed` |
| `scripts/cleanup_old_scans.py` | Nettoyer DB | `--keep N` |
| `scripts/start_dashboard.sh` | Lancer dashboard | Aucune |

### Tests

#### Exécution des tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_scanner.py
pytest tests/test_stats.py

# Avec couverture
pytest --cov=src --cov-report=html
```

#### Tests disponibles

| Fichier | Nombre de tests | Couverture |
|---------|-----------------|------------|
| `tests/test_scanner.py` | 15 | Scanner + Database |
| `tests/test_stats.py` | 18 | Statistiques |
| `tests/test_utils.py` | 10 | Utilitaires |
| `tests/test_integration.py` | 8 | Intégration complète |
| **Total** | **51** | **~85%** |


### Ressources

- **Email support** : regis.gallon@lecnam.net

### Contribuer

Les contributions sont les bienvenues ! Voir `CONTRIBUTING.md`.

### Licence

Ce projet est sous licence MIT. Voir fichier [`LICENSE`](LICENSE).

---

**Documentation mise à jour le 4 octobre 2025**

*Pour toute question, consulter d'abord [`GUIDE_DEMARRAGE.md`](GUIDE_DEMARRAGE.md) ou [`DASHBOARD_QUICKSTART.md`](DASHBOARD_QUICKSTART.md).*