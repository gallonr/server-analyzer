#!/bin/bash
# Script de lancement du dashboard

cd "$(dirname "$0")/.."

# Activer environnement
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Environnement virtuel non trouvé. Création..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Vérifier Streamlit installé
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit non installé"
    echo "Installation..."
    pip install streamlit plotly
fi

# Vérifier que la base de données existe
if [ ! -f "data/server_analysis.db" ]; then
    echo "⚠️  Base de données introuvable: data/server_analysis.db"
    echo "💡 Lancez d'abord un scan avec: python scripts/run_scan.py"
    echo ""
    echo "Voulez-vous continuer quand même ? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Lancer dashboard
echo "🚀 Lancement du dashboard..."
echo "📊 Accessible sur: http://localhost:8501"
echo "🛑 Pour arrêter: Ctrl+C"
echo ""

streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
