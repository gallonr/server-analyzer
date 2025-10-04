# Guide SSH - Server Analyzer

## Informations de connexion

**Serveur distant** : `rgallon@195.83.28.108`

## Configuration SSH (recommandé)

Pour faciliter les connexions, configurez un alias SSH :

### 1. Éditer le fichier de config SSH

```bash
nano ~/.ssh/config
```

### 2. Ajouter cette configuration

```
Host server-analyzer
    HostName 195.83.28.108
    User rgallon
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 3. Utiliser l'alias

Maintenant vous pouvez simplement utiliser :

```bash
ssh server-analyzer
scp fichier.py server-analyzer:~/server-analyzer/
```

## Configuration des clés SSH (fortement recommandé)

Pour éviter de taper le mot de passe à chaque fois :

### 1. Générer une clé SSH (si vous n'en avez pas)

```bash
ssh-keygen -t ed25519 -C "server-analyzer"
# Appuyez sur Entrée pour accepter l'emplacement par défaut
# Entrez un mot de passe (optionnel mais recommandé)
```

### 2. Copier la clé sur le serveur

```bash
ssh-copy-id rgallon@195.83.28.108
# ou avec l'alias :
ssh-copy-id server-analyzer
```

### 3. Tester

```bash
ssh server-analyzer
# Vous ne devriez plus avoir besoin du mot de passe
```

## Commandes utiles

### Connexion et navigation

```bash
# Connexion simple
ssh rgallon@195.83.28.108

# Connexion avec alias
ssh server-analyzer

# Exécuter une commande sans se connecter
ssh server-analyzer "ls -la ~/server-analyzer"

# Se connecter et aller directement dans le dossier
ssh -t server-analyzer "cd ~/server-analyzer && bash"
```

### Transfert de fichiers

```bash
# Envoyer un fichier
scp fichier.py server-analyzer:~/server-analyzer/

# Envoyer un dossier
scp -r dossier/ server-analyzer:~/server-analyzer/

# Récupérer un fichier
scp server-analyzer:~/server-analyzer/data/results.db ./

# Récupérer un dossier
scp -r server-analyzer:~/server-analyzer/logs/ ./local_logs/

# Synchronisation avec rsync (plus efficace)
rsync -avz --progress server-analyzer:~/server-analyzer/data/ ./local_data/
```

### Édition de fichiers à distance

```bash
# Éditer directement avec nano
ssh server-analyzer "nano ~/server-analyzer/config.yaml"

# Ou se connecter et éditer
ssh server-analyzer
cd ~/server-analyzer
nano config.yaml
```

### Surveillance en temps réel

```bash
# Voir les logs en temps réel
ssh server-analyzer "tail -f ~/server-analyzer/logs/scan_*.log"

# Surveiller l'utilisation CPU/Mémoire
ssh server-analyzer "htop"

# Voir l'espace disque
ssh server-analyzer "df -h"

# Voir les processus Python
ssh server-analyzer "ps aux | grep python"
```

## Sessions persistantes avec screen/tmux

Pour lancer des processus longs qui continuent après déconnexion :

### Avec screen

```bash
# Se connecter au serveur
ssh server-analyzer

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
ssh server-analyzer
screen -r scan

# Lister toutes les sessions screen
screen -ls

# Tuer une session
screen -X -S scan quit
```

### Avec tmux

```bash
# Se connecter au serveur
ssh server-analyzer

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
ssh server-analyzer

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
    
    ssh server-analyzer << 'EOF'
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
ping 195.83.28.108

# Tester SSH avec verbosité
ssh -v rgallon@195.83.28.108

# Vérifier le port SSH
nc -zv 195.83.28.108 22
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
