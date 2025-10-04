# Guide SSH - Server Analyzer

## Informations de connexion

**Serveur distant** : `user@domain`

## Configuration SSH (recommandé)

Pour faciliter les connexions, configurez un alias SSH :

### 1. Éditer le fichier de config SSH

```bash
nano ~/.ssh/config
```

### 2. Ajouter cette configuration

```
Host serverAnalyse
    HostName A DEFINIR
    User user
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 3. Utiliser l'alias

Maintenant vous pouvez simplement utiliser :

```bash
ssh serverAnalyse
scp fichier.py sserverAnalyse:~/server-analyzer/
```

## Configuration des clés SSH (fortement recommandé)

Pour éviter de taper le mot de passe à chaque fois :

### 1. Générer une clé SSH (si vous n'en avez pas)

```bash
ssh-keygen -t ed25519 -C "serverAnalyse"
# Appuyez sur Entrée pour accepter l'emplacement par défaut
# Entrez un mot de passe (optionnel mais recommandé)
```

### 2. Copier la clé sur le serveur

```bash
ssh-copy-id user@domain
# ou avec l'alias :
ssh-copy-id serverAnalyse
```

### 3. Tester

```bash
ssh serverAnalyse
# Vous ne devriez plus avoir besoin du mot de passe
```

## Commandes utiles

### Connexion et navigation

```bash
# Connexion simple
ssh user@domain

# Connexion avec alias
ssh serveurAnalyse

# Exécuter une commande sans se connecter
ssh serveurAnalyse "ls -la ~/server-analyzer"

# Se connecter et aller directement dans le dossier
ssh -t serveurAnalyse "cd ~/server-analyzer && bash"
```

### Transfert de fichiers

```bash
# Envoyer un fichier
scp fichier.py serveurAnalyse:~/server-analyzer/

# Envoyer un dossier
scp -r dossier/ serveurAnalyse:~/server-analyzer/

# Récupérer un fichier
scp serveurAnalyse:~/server-analyzer/data/results.db ./

# Récupérer un dossier
scp -r serveurAnalyse:~/server-analyzer/logs/ ./local_logs/

# Synchronisation avec rsync (plus efficace)
rsync -avz --progress serveurAnalyse:~/server-analyzer/data/ ./local_data/
```

### Édition de fichiers à distance

```bash
# Éditer directement avec nano
ssh serveurAnalyse "nano ~/server-analyzer/config.yaml"

# Ou se connecter et éditer
ssh serveurAnalyse
cd ~/server-analyzer
nano config.yaml
```

### Surveillance en temps réel

```bash
# Voir les logs en temps réel
ssh serveurAnalyse "tail -f ~/server-analyzer/logs/scan_*.log"

# Surveiller l'utilisation CPU/Mémoire
ssh serveurAnalyse "htop"

# Voir l'espace disque
ssh serveurAnalyse "df -h"

# Voir les processus Python
ssh serveurAnalyse "ps aux | grep python"
```

## Sessions persistantes avec screen/tmux

Pour lancer des processus longs qui continuent après déconnexion :

### Avec screen

```bash
# Se connecter au serveur
ssh serveurAnalyse

# Démarrer une session screen
screen -S scan

# Lancer votre script
cd ~/server-analyzer
source venv/bin/activate
python scripts/run_scan.py

# Détacher la session : Ctrl+A puis D

# Se déconnecter du serveur
exit

# Plus tard, se reconnecter et réattacher
ssh serveurAnalyse
screen -r scan

# Lister toutes les sessions screen
screen -ls

# Tuer une session
screen -X -S scan quit
```

### Avec tmux

```bash
# Se connecter au serveur
ssh serveurAnalyse

# Démarrer une session tmux
tmux new -s scan

# Lancer votre script
cd ~/server-analyzer
source venv/bin/activate
python scripts/run_scan.py

# Détacher la session : Ctrl+B puis D

# Réattacher
tmux attach -t scan

# Lister les sessions
tmux ls
```

## Exécution en arrière-plan avec nohup

```bash
ssh serveurAnalyse

cd ~/server-analyzer
source venv/bin/activate

# Lancer avec nohup
nohup python scripts/run_scan.py > logs/scan.log 2>&1 &

# Vérifier que ça tourne
ps aux | grep run_scan.py

# Voir les logs
tail -f logs/scan.log

# Arrêter le processus
pkill -f run_scan.py
```

## Monitoring distant

### Créer un script de monitoring

Sur votre machine locale :

```bash
#!/bin/bash
# monitor_remote.sh

while true; do
    clear
    echo "=== Server Analyzer - Status ==="
    echo ""
    
    ssh serveurAnalyse << 'EOF'
cd ~/server-analyzer
echo "📊 Processus Python actifs:"
ps aux | grep python | grep -v grep
echo ""
echo "💾 Espace disque:"
df -h ~/server-analyzer/data
echo ""
echo "📝 Dernières lignes du log:"
tail -5 logs/scan_*.log 2>/dev/null || echo "Pas de logs"
EOF
    
    sleep 30
done
```

## Troubleshooting

### Connexion refuse/timeout

```bash
# Tester la connectivité
ping IP

# Tester SSH avec verbosité
ssh -v user@domain

# Vérifier le port SSH
nc -zv IP PORT
```

### Clés SSH ne fonctionnent pas

```bash
# Vérifier les permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Vérifier que la clé est chargée
ssh-add -l

# Ajouter la clé
ssh-add ~/.ssh/id_ed25519
```

### Session screen/tmux perdue

```bash
# Lister toutes les sessions
screen -ls
# ou
tmux ls

# Si une session "Attached" est bloquée
screen -D -r nom_session
# ou
tmux attach -d -t nom_session
```

## Bonnes pratiques

1. **Toujours utiliser screen/tmux** pour les longs traitements
2. **Configurer les clés SSH** pour éviter les mots de passe
3. **Surveiller l'espace disque** régulièrement
4. **Faire des sauvegardes** des résultats importants
5. **Vérifier les logs** après chaque exécution
6. **Utiliser rsync** plutôt que scp pour les gros transferts

## Scripts utiles

Tous les scripts fournis :

- `deploy.sh` : Déployer le code sur le serveur
- `connect.sh` : Connexion rapide au serveur
- `activate.sh` : Activer l'environnement Python (sur le serveur)
