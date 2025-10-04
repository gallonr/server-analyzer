#!/bin/bash
#
# Script d'installation environnement virtuel Python
# Pour serveur Debian/Ubuntu avec environnement protégé
#

set -e

echo "=========================================="
echo "  Installation Environnement Virtuel"
echo "  Programme d'analyse serveur 28 To"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Vérifier que python3-venv est installé
echo "1. Vérification python3-venv..."
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}⚠️  python3-venv non installé${NC}"
    echo "Installation avec sudo..."
    sudo apt update
    sudo apt install -y python3-venv python3-full
else
    echo -e "${GREEN}✅ python3-venv installé${NC}"
fi

echo ""
echo "2. Création environnement virtuel 'venv'..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Environnement 'venv' existe déjà${NC}"
    read -p "Supprimer et recréer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✅ Environnement recréé${NC}"
    else
        echo "Conservation environnement existant"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement créé${NC}"
fi

echo ""
echo "3. Activation environnement..."
source venv/bin/activate

echo -e "${GREEN}✅ Environnement activé${NC}"
echo "   Python: $(which python)"
echo "   Version: $(python --version)"

echo ""
echo "4. Mise à jour pip..."
pip install --upgrade pip

echo ""
echo "5. Installation dépendances depuis requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Toutes les dépendances installées${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt non trouvé${NC}"
    echo "Installation manuelle des dépendances principales..."
    pip install streamlit pandas plotly pyyaml openpyxl
fi

echo ""
echo "=========================================="
echo "  ✅ INSTALLATION TERMINÉE"
echo "=========================================="
echo ""
echo "Pour utiliser l'environnement :"
echo ""
echo "  # Activer"
echo "  source venv/bin/activate"
echo ""
echo "  # Lancer dashboard"
echo "  streamlit run src/dashboard/app.py"
echo ""
echo "  # Lancer scan"
echo "  python scripts/run_scan.py"
echo ""
echo "  # Désactiver"
echo "  deactivate"
echo ""
echo "📝 L'environnement 'venv' est créé et prêt !"
echo ""
