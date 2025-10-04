# Guide de Démarrage Rapide - Dashboard Phase 3.1

## 🚀 Lancement du Dashboard

### Prérequis

1. **Python 3.10+** installé
2. **Base de données** existante avec au moins un scan
3. **Dépendances** installées

### Installation rapide

```bash
cd /home/rgallon/Documents/RECHERCHE/GestionServeurIntechmer/server-analyzer

# Créer et activer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
```

### Lancer le dashboard

**Méthode 1 : Script automatique (recommandé)**

```bash
./scripts/start_dashboard.sh
```

**Méthode 2 : Commande manuelle**

```bash
source venv/bin/activate
streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

### Accès au dashboard

Une fois lancé, ouvrez votre navigateur :

```
http://localhost:8501
```

---

## 📊 Fonctionnalités Disponibles (Phase 3.1)

### Page Vue d'ensemble

1. **Métriques Globales**
   - Total fichiers
   - Taille totale
   - Nombre de dossiers
   - Durée du scan

2. **Graphiques Principaux**
   - Top 10 extensions par volume (bar chart)
   - Top 10 propriétaires par volume (bar chart)
   - Distribution des tailles de fichiers

3. **Visualisations Avancées**
   - **Onglet Répartition** : Pie chart des extensions
   - **Onglet Hiérarchie** : Treemap des volumes par dossier
   - **Onglet Temporel** : Timeline de création des fichiers

### Navigation

- **Sidebar gauche** : Sélection du scan et navigation
- **4 pages** disponibles :
  - 🏠 Vue d'ensemble (complète)
  - 🔍 Explorateur (à venir Phase 3.2)
  - 🔄 Comparaisons (à venir Phase 3.2)
  - 💾 Exports (à venir Phase 3.2)

---

## 🔧 Configuration

### Fichier de configuration : `.streamlit/config.toml`

Déjà configuré avec :
- Theme clair professionnel
- Port 8501
- Cache optimisé
- Hot-reload activé

### Base de données

Le dashboard cherche automatiquement la base de données dans :
```
data/server_analysis.db
```

Vous pouvez modifier le chemin dans `config.yaml` :
```yaml
database:
  path: data/server_analysis.db
```

---

## ⚡ Performance

### Cache Streamlit

Les données sont mises en cache pendant **5 minutes** (300s) pour améliorer les performances :
- `get_scan_info()` : Infos globales scan
- `get_top_extensions()` : Top extensions
- `get_top_owners()` : Top propriétaires
- `get_size_distribution()` : Distribution tailles
- `get_directory_hierarchy()` : Hiérarchie dossiers
- `get_temporal_data()` : Données temporelles

### Rafraîchir les données

Cliquez sur le bouton **"🔄 Rafraîchir les données"** en bas de la page Overview pour vider le cache et recharger.

---

## 🐛 Résolution de problèmes

### Erreur : Base de données introuvable

```
❌ Base de données introuvable: data/server_analysis.db
```

**Solution** : Lancez d'abord un scan :
```bash
python scripts/run_scan.py
```

### Erreur : Aucun scan disponible

```
❌ Aucun scan disponible
```

**Solution** : La base existe mais ne contient aucun scan. Lancez :
```bash
python scripts/run_scan.py
```

### Erreur : Module non trouvé

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution** : Installez les dépendances :
```bash
pip install -r requirements.txt
```

### Port 8501 déjà utilisé

**Solution** : Changez le port dans la commande :
```bash
streamlit run src/dashboard/app.py --server.port 8502
```

---

## 📝 Structure des Données

### Table `scans`

Le dashboard affiche les scans depuis la table `scans` :
```sql
SELECT scan_id, start_time, total_files
FROM scans
ORDER BY start_time DESC
```

### Table `files`

Les statistiques sont calculées depuis la table `files` :
- Extensions
- Propriétaires
- Tailles
- Dates

---

## 🎯 Prochaines Étapes

La Phase 3.1 est complète. Les prochaines fonctionnalités (Phase 3.2) incluront :

1. **Page Explorateur** : Navigation dans l'arborescence
2. **Filtres dynamiques** : Filtrer par taille, date, propriétaire, etc.
3. **Page Comparaisons** : Comparer deux scans
4. **Page Exports** : Exporter en CSV, Excel, PDF

---

## 💡 Conseils d'utilisation

### Pour une meilleure expérience

1. **Mode plein écran** : Le dashboard utilise le layout "wide" pour maximiser l'espace
2. **Thème** : Le thème clair est configuré par défaut
3. **Tooltips** : Survolez les graphiques pour plus de détails
4. **Tabs** : Utilisez les onglets pour organiser les visualisations

### Raccourcis clavier

- **Ctrl+C** dans le terminal : Arrêter le dashboard
- **R** dans le navigateur : Rafraîchir la page
- **Ctrl+K** : Ouvrir la palette de commandes Streamlit

---

*Guide créé le 4 octobre 2025 - Phase 3.1*
