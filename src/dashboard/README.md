# Dashboard Streamlit - Documentation

## 📊 Vue d'ensemble

Le dashboard Streamlit est l'interface web interactive pour visualiser et explorer les résultats des scans du serveur.

## 🏗️ Architecture

```
src/dashboard/
├── app.py                          # Point d'entrée principal
│   ├── Configuration Streamlit
│   ├── Connexion base de données
│   ├── Sélection scan
│   └── Navigation multi-pages
│
└── components/
    ├── overview.py                 # Page Vue d'ensemble
    │   ├── Métriques globales
    │   ├── Graphiques standards
    │   └── Visualisations avancées
    │
    ├── charts.py                   # Graphiques réutilisables
    │   ├── Pie chart extensions
    │   ├── Treemap hiérarchique
    │   └── Timeline temporelle
    │
    ├── explorer.py                 # Navigation arborescence (Phase 3.2)
    ├── comparisons.py              # Comparaison scans (Phase 3.2)
    └── exports.py                  # Exports données (Phase 3.2)
```

## 🚀 Lancement

### Prérequis

- Python 3.10+
- Base de données SQLite avec au moins un scan
- Dépendances installées (`requirements.txt`)

### Commandes

```bash
# Méthode 1 : Script automatique
./scripts/start_dashboard.sh

# Méthode 2 : Manuel
streamlit run src/dashboard/app.py
```

Accessible sur : **http://localhost:8501**

## 📦 Dépendances

```
streamlit>=1.28.0      # Framework web
plotly>=5.17.0         # Graphiques interactifs
pandas>=2.0.0          # Manipulation données
pyyaml>=6.0            # Config YAML
```

## 🎨 Pages

### 1. Vue d'ensemble (✅ Phase 3.1)

**Métriques globales**
- Total fichiers
- Taille totale
- Nombre dossiers
- Durée scan

**Graphiques standards**
- Top 10 extensions (bar chart)
- Top 10 propriétaires (bar chart)
- Distribution tailles (histogram)

**Visualisations avancées (tabs)**
- Répartition : Pie chart extensions
- Hiérarchie : Treemap volumes
- Temporel : Timeline double axe

### 2. Explorateur (🔜 Phase 3.2)

- Navigation arborescence
- Drill-down dossiers
- Tableau fichiers
- Filtres dynamiques

### 3. Comparaisons (🔜 Phase 3.2)

- Comparer 2 scans
- Détection changements
- Évolution volumes

### 4. Exports (🔜 Phase 3.2)

- Export CSV
- Export Excel
- Rapports PDF

## 🔧 Configuration

### Fichier `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### Base de données

Chemin configuré dans `config.yaml` :

```yaml
database:
  path: data/server_analysis.db
```

Le dashboard charge automatiquement ce fichier.

## ⚡ Performance

### Cache Streamlit

Toutes les requêtes SQL sont mises en cache avec `@st.cache_data(ttl=300)` :

- **TTL** : 5 minutes (300 secondes)
- **Invalidation** : Automatique ou bouton "Rafraîchir"
- **Scope** : Par scan_id

**Fonctions cachées** :
- `get_scan_info()` : Infos globales
- `get_top_extensions()` : Top extensions
- `get_top_owners()` : Top propriétaires
- `get_size_distribution()` : Distribution tailles
- `get_directory_hierarchy()` : Hiérarchie dossiers
- `get_temporal_data()` : Données temporelles

### Optimisations SQL

- Index sur colonnes clés (extension, owner_name, size_bytes, mtime)
- GROUP BY optimisé
- LIMIT sur requêtes volumineuses
- Préfiltrage WHERE sur scan_id

## 📊 Graphiques Plotly

### Types de graphiques

| Type | Usage | Interactivité |
|------|-------|---------------|
| **Bar Chart** | Top N, comparaisons | Hover, zoom |
| **Pie Chart** | Répartitions | Hover, légende |
| **Treemap** | Hiérarchies | Drill-down, hover |
| **Timeline** | Évolution temporelle | Zoom, pan, hover |

### Personnalisation

Tous les graphiques supportent :
- **Tooltips** personnalisés avec données formatées
- **Couleurs** thématiques cohérentes
- **Responsive** : s'adaptent à la largeur du container
- **Export** : télécharger en PNG depuis le menu Plotly

## 🔍 Requêtes SQL

### Exemples de requêtes

**Top extensions** :
```sql
SELECT 
    COALESCE(extension, 'sans_extension') as extension,
    COUNT(*) as file_count,
    SUM(size_bytes) as total_size
FROM files
WHERE scan_id = ? AND is_directory = 0
GROUP BY extension
ORDER BY total_size DESC
LIMIT 10
```

**Distribution tailles** :
```sql
SELECT 
    CASE 
        WHEN size_bytes < 1024 THEN '< 1 KB'
        WHEN size_bytes < 1048576 THEN '1 KB - 1 MB'
        WHEN size_bytes < 10485760 THEN '1 MB - 10 MB'
        WHEN size_bytes < 104857600 THEN '10 MB - 100 MB'
        WHEN size_bytes < 1073741824 THEN '100 MB - 1 GB'
        ELSE '> 1 GB'
    END as size_category,
    COUNT(*) as count
FROM files
WHERE scan_id = ? AND is_directory = 0
GROUP BY size_category
ORDER BY size_category
```

## 🐛 Débogage

### Logs Streamlit

Streamlit affiche les logs dans la console :

```bash
# Lancer avec niveau DEBUG
streamlit run src/dashboard/app.py --logger.level=debug
```

### Logs application

Les logs applicatifs sont configurés dans `app.py` :

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')
```

### Erreurs courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| Base introuvable | Aucun scan effectué | Lancer `run_scan.py` |
| Aucun scan | Table scans vide | Compléter un scan |
| Module non trouvé | Dépendances manquantes | `pip install -r requirements.txt` |
| Port occupé | 8501 déjà utilisé | Changer port avec `--server.port` |

## 🧪 Tests

### Tests manuels (Phase 3.1)

```bash
# 1. Lancer dashboard
./scripts/start_dashboard.sh

# 2. Navigateur : http://localhost:8501

# 3. Vérifier :
# ✅ Page charge sans erreur
# ✅ Sélecteur scan visible
# ✅ Navigation fonctionne
# ✅ Métriques affichées
# ✅ Tous graphiques s'affichent
# ✅ Tooltips fonctionnels
# ✅ Bouton refresh fonctionne
# ✅ Performance < 3s chargement
```

### Tests automatisés (à venir)

Phase 4 inclura tests unitaires et d'intégration :
- `tests/test_dashboard.py` : Tests composants
- `tests/test_charts.py` : Tests graphiques
- Selenium pour tests UI

## 📝 Conventions de code

### Structure des composants

```python
# 1. Imports
import streamlit as st
import plotly.graph_objects as go

# 2. Fonctions de récupération données (avec cache)
@st.cache_data(ttl=300)
def get_data(_db, scan_id: str):
    ...

# 3. Fonctions de visualisation
def display_chart(df: pd.DataFrame):
    ...

# 4. Fonction render principale
def render_page(db, scan_id: str):
    st.title("...")
    ...
```

### Nommage

- Fonctions récupération : `get_*`
- Fonctions affichage : `display_*` ou `render_*`
- Cache : toujours préfixer `_db` pour éviter hashing

### Documentation

- Docstrings Google style
- Types hints systématiques
- Commentaires pour logique complexe

## 🔄 Workflow développement

### Hot-reload

Streamlit recharge automatiquement à chaque modification :

1. Modifier fichier Python
2. Sauvegarder
3. Streamlit détecte et propose reload

### Debugging

```python
# Afficher données dans sidebar
st.sidebar.write(df)

# Debug box
st.expander("Debug"):
    st.write(data)

# Stop execution
st.stop()
```

## 📚 Ressources

- [Streamlit Docs](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [Pandas Docs](https://pandas.pydata.org/docs/)

## 🎯 Roadmap

### Phase 3.1 (✅ Complétée)
- Configuration multi-pages
- Page Overview complète
- Graphiques avancés

### Phase 3.2 (🔜 Prochaine)
- Page Explorer
- Filtres dynamiques
- Page Comparaisons
- Page Exports

### Phase 3.3 (🔮 Future)
- Authentification
- Partage dashboards
- Alertes temps réel
- Mode sombre

---

*Documentation créée le 4 octobre 2025 - Phase 3.1*
