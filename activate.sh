#!/bin/bash
# Script d'activation rapide de l'environnement

source venv/bin/activate
echo "✓ Environnement Python activé"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"
