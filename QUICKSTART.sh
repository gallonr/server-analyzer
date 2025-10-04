#!/bin/bash
# Guide de démarrage rapide - Server Analyzer
# Affichage des commandes essentielles

cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║          SERVER ANALYZER - Guide de Démarrage Rapide         ║
║                    Phase 0 : Terminée ✓                      ║
╚══════════════════════════════════════════════════════════════╝

📋 ÉTAT DU PROJET
  ✓ Structure créée
  ✓ Environnement Python configuré (venv/)
  ✓ Dépendances installées
  ✓ Configuration prête
  ✓ Tests fonctionnent (3/3 passed)
  ✓ Scripts de déploiement SSH créés

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 DÉMARRAGE RAPIDE

1️⃣  EN LOCAL (développement)
   
   # Activer environnement Python
   source venv/bin/activate
   
   # Tester la configuration
   python src/config_validator.py
   
   # Lancer les tests
   pytest

2️⃣  DÉPLOYER SUR SERVEUR DISTANT (rgallon@195.83.28.108)
   
   # Déploiement automatique
   ./deploy.sh
   
   # Ou connexion manuelle
   ./connect.sh

3️⃣  SUR LE SERVEUR (après déploiement)
   
   # Se connecter
   ssh rgallon@195.83.28.108
   
   # Aller dans le projet
   cd ~/server-analyzer
   
   # Activer environnement
   source venv/bin/activate
   
   # Configurer les chemins à scanner
   nano config.yaml
   # Modifier la section root_paths avec les vrais chemins
   
   # Tester la configuration
   python src/config_validator.py
   
   # Lancer le scan (quand Phase 1 sera développée)
   # screen -S scan
   # python scripts/run_scan.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 FICHIERS IMPORTANTS

  Config & Setup:
    config.yaml           Configuration principale (à éditer)
    config.yaml.example   Exemple de configuration
    requirements.txt      Dépendances Python
    
  Scripts:
    activate.sh          Active l'environnement Python (local)
    deploy.sh            Déploie sur le serveur distant
    connect.sh           Se connecte au serveur
    
  Documentation:
    README.md            Vue d'ensemble et installation
    SSH_GUIDE.md         Guide complet SSH et déploiement
    SERVEUR_CONFIG.md    Configuration serveur spécifique
    PHASE0_RAPPORT.md    Rapport Phase 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  CONFIGURATION SERVEUR

  Serveur:      rgallon@195.83.28.108
  Chemin:       ~/server-analyzer
  
  ⚠️  IMPORTANT: Avant le premier scan
  
  1. Identifier les chemins à scanner sur le serveur:
     ssh rgallon@195.83.28.108 "df -h"
     
  2. Modifier config.yaml avec les vrais chemins:
     ssh rgallon@195.83.28.108
     cd ~/server-analyzer
     nano config.yaml
     
  3. Ajuster num_workers selon les cœurs disponibles:
     nproc  # Voir nombre de cœurs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 COMMANDES UTILES

  Local:
    source venv/bin/activate     Active l'environnement
    pytest                        Lance les tests
    ./deploy.sh                   Déploie sur serveur
    ./connect.sh                  Se connecte au serveur
    
  SSH:
    ssh rgallon@195.83.28.108                        Connexion
    scp config.yaml rgallon@195.83.28.108:~/...      Copier fichier
    ssh rgallon@... "tail -f ~/...logs/scan*.log"    Voir logs
    
  Sur serveur:
    cd ~/server-analyzer                  Aller dans projet
    source venv/bin/activate              Activer venv
    python src/config_validator.py        Tester config
    screen -S scan                        Session persistante
    screen -r scan                        Réattacher session

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 DOCUMENTATION COMPLÈTE

  Tout est documenté dans:
    - README.md            : Installation et usage
    - SSH_GUIDE.md         : Guide SSH complet
    - SERVEUR_CONFIG.md    : Configuration serveur
    - PHASE0_RAPPORT.md    : Rapport Phase 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PROCHAINE ÉTAPE: PHASE 1

  La Phase 0 est terminée ✓
  
  Phase 1 : Développer le scanner et la base de données
    - src/scanner.py
    - src/database.py
    - scripts/run_scan.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
