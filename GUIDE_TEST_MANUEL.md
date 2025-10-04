# Guide de Test Manuel - Phase 3.3

**Projet** : Programme d'analyse serveur 28 To  
**Phase** : 3.3 - Tests Manuels Dashboard  
**Date** : 4 octobre 2025  
**Durée estimée** : 30 minutes

---

## 🎯 Objectif

Valider manuellement toutes les fonctionnalités de la Phase 3.3 :
- Page Exports
- Page Comparaisons
- Script CLI Export

---

## ⚙️ Pré-requis

### 1. Environnement

```bash
cd server-analyzer
source venv/bin/activate  # ou votre environnement virtuel
```

### 2. Base de données

**Vérifier qu'au moins 2 scans existent** :

```bash
python scripts/export_results.py --list
```

**Si < 2 scans, en lancer** :

```bash
# Premier scan
python scripts/run_scan.py --root /chemin/test1

# Deuxième scan (modifier légèrement les données si test local)
python scripts/run_scan.py --root /chemin/test2
```

---

## 📋 Tests à effectuer

### TEST 1 - Page Exports CSV ✅

**Objectif** : Vérifier export CSV fonctionne

**Étapes** :
1. Lancer dashboard : `streamlit run src/dashboard/app.py`
2. Sélectionner un scan dans sidebar
3. Naviguer vers page **"💾 Exports"**
4. Sélectionner format **CSV**
5. Cliquer **"🚀 Générer export"**
6. Cliquer **"⬇️ Télécharger CSV"**
7. Ouvrir fichier avec Excel/LibreOffice

**Résultat attendu** :
- [ ] Bouton téléchargement apparaît
- [ ] Fichier CSV téléchargé
- [ ] Contient colonnes : path, name, extension, size_bytes, owner_name, etc.
- [ ] Colonnes formatées : size_formatted, mtime_formatted
- [ ] Données correctes

---

### TEST 2 - Page Exports Excel ✅

**Objectif** : Vérifier export Excel avec formatage

**Étapes** :
1. Page Exports
2. Sélectionner format **Excel**
3. Générer export
4. Télécharger
5. Ouvrir avec Excel/LibreOffice

**Résultat attendu** :
- [ ] Fichier .xlsx téléchargé
- [ ] 3 feuilles : Informations, Fichiers, Extensions
- [ ] Feuille "Informations" : Scan ID, dates, totaux
- [ ] Feuille "Fichiers" : Liste fichiers (max 100k)
- [ ] Feuille "Extensions" : Stats par extension
- [ ] Headers formatés (couleur bleue)

---

### TEST 3 - Page Exports JSON ✅

**Objectif** : Vérifier export JSON structuré

**Étapes** :
1. Page Exports
2. Sélectionner format **JSON**
3. Générer export
4. Télécharger
5. Ouvrir avec éditeur texte

**Résultat attendu** :
- [ ] Fichier .json téléchargé
- [ ] Structure : `{scan: {...}, files: [...], export_date, files_count}`
- [ ] Données scan correctes
- [ ] Liste fichiers (max 50k)
- [ ] JSON valide (peut être parsé)

---

### TEST 4 - Page Exports avec Filtres ✅

**Objectif** : Vérifier application filtres dans export

**Étapes** :
1. Page **"🔍 Explorer"**
2. Activer filtres (ex: taille min 1 MB, extension .txt)
3. Revenir page **"💾 Exports"**
4. Cocher **"Appliquer les filtres actifs"**
5. Exporter CSV
6. Vérifier contenu

**Résultat attendu** :
- [ ] Badge "✅ X filtre(s) seront appliqués"
- [ ] Export contient seulement fichiers filtrés
- [ ] Nombre lignes cohérent avec filtres

---

### TEST 5 - Page Comparaisons - Sélection ✅

**Objectif** : Vérifier sélection 2 scans

**Étapes** :
1. Naviguer vers **"🔄 Comparaisons"**
2. Observer liste scans disponibles
3. Sélectionner Scan 1 (dropdown gauche)
4. Sélectionner Scan 2 (dropdown droite)
5. Vérifier infos affichées

**Résultat attendu** :
- [ ] Au moins 2 scans dans dropdowns
- [ ] Format : "ID - Date (X fichiers, Y taille)"
- [ ] Infos scan 1 affichées (date, fichiers, taille)
- [ ] Infos scan 2 affichées
- [ ] Si scans identiques : Warning "scans différents requis"

---

### TEST 6 - Page Comparaisons - Calcul Différentiel ✅

**Objectif** : Vérifier comparaison entre 2 scans

**Étapes** :
1. Sélectionner 2 scans **différents**
2. Cliquer **"🔍 Lancer la comparaison"**
3. Attendre calcul (spinner)
4. Observer résultats

**Résultat attendu** :
- [ ] Calcul terminé en < 10s
- [ ] 4 métriques affichées :
  - Fichiers (avec delta)
  - Taille totale (avec delta)
  - Nouveaux
  - Supprimés
- [ ] Deltas corrects (+ ou -)

---

### TEST 7 - Page Comparaisons - Graphiques ✅

**Objectif** : Vérifier visualisations

**Étapes** :
1. Après comparaison
2. Observer section "📈 Visualisations"
3. Interagir avec graphiques (hover, zoom)

**Résultat attendu** :
- [ ] 2 graphiques affichés côte à côte
- [ ] Graphique 1 : Évolution (barres + ligne, double axe Y)
- [ ] Graphique 2 : Pie chart changements (vert/rouge/orange)
- [ ] Graphiques interactifs (Plotly)
- [ ] Données cohérentes avec métriques

---

### TEST 8 - Page Comparaisons - Tabs Détails ✅

**Objectif** : Vérifier listes fichiers par catégorie

**Étapes** :
1. Cliquer tab **"🆕 Nouveaux fichiers"**
2. Observer tableau
3. Cliquer **"💾 Exporter CSV"** si fichiers présents
4. Répéter pour tabs **"🗑️ Supprimés"** et **"✏️ Modifiés"**

**Résultat attendu** :
- [ ] Tab Nouveaux : Liste fichiers ajoutés (top 1000)
- [ ] Colonnes : name, Taille, owner, Date, path
- [ ] Export CSV fonctionne
- [ ] Tab Supprimés : Liste fichiers retirés
- [ ] Tab Modifiés : Différence taille affichée
- [ ] Si aucun changement : Message "Aucun fichier..."

---

### TEST 9 - Script CLI - Liste Scans ✅

**Objectif** : Vérifier script CLI liste scans

**Étapes** :
```bash
python scripts/export_results.py --list
```

**Résultat attendu** :
- [ ] Tableau formaté affiché
- [ ] Colonnes : Scan ID, Date, Fichiers, Taille
- [ ] Tous scans présents
- [ ] Données formatées (virgules, tailles lisibles)

---

### TEST 10 - Script CLI - Export CSV ✅

**Objectif** : Export CSV en ligne de commande

**Étapes** :
```bash
python scripts/export_results.py \
  --scan-id <SCAN_ID> \
  --format csv \
  --output /tmp/export_test.csv
```

**Résultat attendu** :
- [ ] Message "✅ Export CSV réussi"
- [ ] Fichier créé : `/tmp/export_test.csv`
- [ ] Contenu identique à export dashboard
- [ ] Colonnes formatées présentes

---

### TEST 11 - Script CLI - Export Excel ✅

**Objectif** : Export Excel en ligne de commande

**Étapes** :
```bash
python scripts/export_results.py \
  --scan-id <SCAN_ID> \
  --format excel \
  --output /tmp/export_test.xlsx
```

**Résultat attendu** :
- [ ] Message "✅ Export Excel réussi"
- [ ] Fichier .xlsx créé
- [ ] 2 feuilles : Fichiers, Extensions
- [ ] Ouvre correctement dans Excel

---

### TEST 12 - Script CLI - Gestion Erreurs ✅

**Objectif** : Vérifier messages erreurs

**Étapes** :
```bash
# Scan invalide
python scripts/export_results.py --scan-id INVALIDE --format csv --output /tmp/test.csv

# Sans arguments
python scripts/export_results.py
```

**Résultat attendu** :
- [ ] Message "❌ Scan introuvable"
- [ ] Message "Utilisez --list"
- [ ] Exit code 1
- [ ] Aide affichée si pas d'arguments

---

### TEST 13 - Performance Dashboard ✅

**Objectif** : Vérifier performance générale

**Étapes** :
1. Ouvrir dashboard
2. Naviguer entre pages
3. Lancer comparaison
4. Générer export
5. Observer temps de réponse

**Résultat attendu** :
- [ ] Chargement initial < 3s
- [ ] Navigation pages instantanée
- [ ] Comparaison < 10s
- [ ] Export < 15s (100k lignes)
- [ ] Pas de freeze interface
- [ ] Pas d'erreurs console

---

### TEST 14 - Gestion Erreurs Dashboard ✅

**Objectif** : Vérifier messages erreurs

**Étapes** :
1. Renommer temporairement `data/server_analysis.db`
2. Relancer dashboard
3. Observer messages
4. Restaurer DB

**Résultat attendu** :
- [ ] Message erreur clair
- [ ] Pas de crash dashboard
- [ ] Détails techniques dans expander
- [ ] Suggestion action (vérifier chemin DB)

---

## 📊 Résumé des Tests

### Checklist complète

- [ ] TEST 1 - Export CSV
- [ ] TEST 2 - Export Excel
- [ ] TEST 3 - Export JSON
- [ ] TEST 4 - Export avec filtres
- [ ] TEST 5 - Sélection scans comparaison
- [ ] TEST 6 - Calcul différentiel
- [ ] TEST 7 - Graphiques comparaison
- [ ] TEST 8 - Tabs détails
- [ ] TEST 9 - CLI liste scans
- [ ] TEST 10 - CLI export CSV
- [ ] TEST 11 - CLI export Excel
- [ ] TEST 12 - CLI gestion erreurs
- [ ] TEST 13 - Performance
- [ ] TEST 14 - Gestion erreurs

**Total** : 14 tests

---

## ✅ Validation Finale

### Phase 3.3 validée si :

- [ ] **Tous exports fonctionnent** (CSV, Excel, JSON)
- [ ] **Comparaisons correctes** (nouveaux/supprimés/modifiés)
- [ ] **Graphiques s'affichent**
- [ ] **Script CLI opérationnel**
- [ ] **Performance acceptable** (< 3s chargement)
- [ ] **Gestion erreurs robuste**
- [ ] **Aucun bug critique**

### Critères de succès

| Critère | Minimum | Optimal |
|---------|---------|---------|
| Tests passés | 12/14 (85%) | 14/14 (100%) |
| Performance chargement | < 5s | < 3s |
| Performance comparaison | < 15s | < 10s |
| Bugs critiques | 0 | 0 |

---

## 📝 Rapport de Test

**À compléter après tests** :

```
Date des tests : _______________
Testeur : _______________

Résultats :
- Tests réussis : _____ / 14
- Tests échoués : _____ / 14
- Bugs trouvés : _____

Performance :
- Chargement page : _____ secondes
- Comparaison 2 scans : _____ secondes
- Export CSV (100k) : _____ secondes

Commentaires :
_________________________________________________
_________________________________________________
_________________________________________________

Validation finale : ☐ VALIDÉ  ☐ À CORRIGER

Signature : _______________
```

---

## 🔧 Dépannage

### Problème : Module openpyxl manquant

```bash
pip install openpyxl
```

### Problème : Moins de 2 scans

```bash
# Lancer plusieurs scans
python scripts/run_scan.py --root /chemin1
python scripts/run_scan.py --root /chemin2
```

### Problème : Dashboard ne démarre pas

```bash
# Vérifier dépendances
pip install -r requirements.txt

# Vérifier config
cat config.yaml
```

### Problème : Comparaison très lente

- Vérifier index SQL présents
- Réduire nombre fichiers dans DB de test
- Vérifier ressources système (RAM, CPU)

---

**Bonne chance avec les tests !** 🎯

*Pour questions : consulter PHASE3-3_RAPPORT.md*
