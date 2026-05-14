# Serveur MCP Duplicati

Serveur MCP (Model Context Protocol) pour gérer les sauvegardes Duplicati depuis un LLM.

[English version](README.md)

## Architecture

Le serveur enveloppe l'API REST de Duplicati et l'expose via le protocole MCP. Deux transports sont disponibles :

- **stdio** — pour une utilisation locale via Claude Code (pas de réseau, pas de port)
- **Streamable HTTP** — pour un déploiement Docker, accessible sur le réseau

## Démarrage

### Utilisation locale avec Claude Code (stdio)

La façon la plus simple de démarrer. Le fichier `.mcp.json` à la racine du projet gère tout automatiquement :

```bash
# Installer uv si nécessaire
brew install uv

# Claude Code détecte automatiquement .mcp.json et lance le serveur
```

Configurer l'URL et le mot de passe Duplicati dans `.mcp.json` :

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "duplicati-mcp"],
      "env": {
        "DUPLICATI_URL": "http://localhost:8200",
        "DUPLICATI_PASSWORD": "votre-mot-de-passe",
        "DUPLICATI_READONLY": ""
      }
    }
  }
}
```

### Avec Docker Compose (image Docker Hub)

```bash
# Éditer DUPLICATI_URL et DUPLICATI_PASSWORD dans docker-compose.yml, puis :
docker compose up -d
```

### Avec Docker Compose (build local)

```bash
# Dans docker-compose.yml : commenter la ligne `image:` et décommenter `build: .`
docker compose up -d --build
```

### Docker direct

```bash
docker run -d \
  --name duplicati-mcp-server \
  -p 3000:3000 \
  -e DUPLICATI_URL=http://votre-host-duplicati:8200 \
  -e DUPLICATI_PASSWORD=votre-mot-de-passe \
  kcofoni/duplicati-mcp:latest
```

### Vérification

```bash
# Vérifier que le serveur tourne
docker logs duplicati-mcp-server

# Tester l'endpoint MCP
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

## Configuration client

### Claude Code — local (stdio)

Pour une utilisation locale sans Docker, ajouter dans le `.mcp.json` du projet :

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "duplicati-mcp"],
      "env": {
        "DUPLICATI_URL": "http://localhost:8200",
        "DUPLICATI_READONLY": ""
      }
    }
  }
}
```

Les credentials sont chargés depuis le fichier `.env` à la racine du projet (voir [Démarrage](#démarrage)).

### Claude Code — Docker/distant (HTTP)

Ajouter dans `.mcp.json` :

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "http",
      "url": "http://votre-host:3000/mcp"
    }
  }
}
```

### Claude Desktop

Claude Desktop nécessite `mcp-proxy` comme pont vers les serveurs HTTP. Ajouter dans le fichier de configuration :

**macOS** : `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows** : `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "duplicati": {
      "command": "uvx",
      "args": ["mcp-proxy", "--transport", "streamablehttp", "http://votre-host:3000/mcp"]
    }
  }
}
```

## Outils disponibles

Une fois connecté, le LLM a accès à :

### Gestion des sauvegardes
1. **list_backups** — Lister tous les jobs configurés avec ID, nom, date et résultat du dernier run
2. **get_backup** — Détails d'un job spécifique
3. **run_backup** — Déclencher immédiatement un job de sauvegarde
4. **abort_backup** — Interrompre la sauvegarde en cours pour un job

### Statut et progression
5. **get_progress** — Progression en temps réel de la tâche active (phase, %, compteurs)
6. **get_server_status** — État du serveur Duplicati, version et tâche active

### Configuration
7. **export_backup_config** — Exporter la configuration d'un job en JSON
8. **update_backup_config** — Mettre à jour une configuration existante en place (utiliser avec `export_backup_config` pour modifier sources, settings, schedule, etc.)
9. **import_backup_config** — Importer une configuration de job depuis un JSON (crée un nouveau job)

### Historique et diagnostics (SQLite — nécessite `DUPLICATI_DB_PATH`)
10. **db_get_backup_metadata** — Métadonnées riches depuis la base locale : date du dernier run, durée, compteurs de fichiers, quota, dernière erreur
11. **db_get_backup_schedule** — Configuration de planification d'un job
12. **db_list_errors** — Journal des erreurs récentes, filtrable par job
13. **db_list_notifications** — Notifications système (alertes de mise à jour, etc.)
14. **db_get_backup_options** — Options de configuration d'un job (compression, politique de rétention, etc.) — les passphrases sont exclues
15. **db_list_operations** — Historique des opérations d'un job (Backup, Restore, List, etc.) avec horodatage
16. **db_get_operation_log** — Résultat complet et statistiques d'une opération spécifique
17. **db_list_filesets** — Points de restauration disponibles (versions) pour un job

## Exemples de prompts

Une fois le serveur connecté à votre LLM, voici des prompts à utiliser :

**État général**
- "Quels jobs de sauvegarde sont configurés sur mon Duplicati ?"
- "Quelle est la dernière sauvegarde qui a été exécutée et quel était son résultat ?"
- "Est-ce qu'une sauvegarde est en cours en ce moment ?"

**Historique et statistiques** _(nécessite `DUPLICATI_DB_PATH`)_
- "Donne-moi l'historique des 10 dernières opérations du job 2"
- "Quelle est la durée moyenne des sauvegardes récentes ?"
- "Y a-t-il eu des erreurs sur mes sauvegardes ces dernières semaines ?"
- "Combien de fichiers sont sauvegardés et quelle est la taille totale occupée sur la destination ?"

**Points de restauration** _(nécessite `DUPLICATI_DB_PATH`)_
- "Quels points de restauration sont disponibles pour mon job de sauvegarde ?"
- "Quelle est la sauvegarde la plus ancienne disponible pour une restauration ?"

**Configuration** _(nécessite `DUPLICATI_DB_PATH`)_
- "Quelle est la politique de rétention configurée sur mon job de sauvegarde ?"
- "Quelles sont les options de compression et de chiffrement utilisées ?"

**Diagnostic** _(nécessite `DUPLICATI_DB_PATH`)_
- "Y a-t-il des notifications système en attente sur Duplicati ?"
- "Mon Duplicati a-t-il rencontré des erreurs récemment ? Lesquelles ?"
- "Analyse la dernière sauvegarde et dis-moi si tout s'est bien passé"

**Question ouverte** _(combine plusieurs outils)_
- "Fais-moi un bilan de santé complet de mes sauvegardes Duplicati"

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DUPLICATI_URL` | `http://localhost:8200` | URL de l'instance Duplicati |
| `DUPLICATI_PASSWORD` | _(vide)_ | Mot de passe de l'interface web Duplicati (laisser vide si aucun) |
| `DUPLICATI_READONLY` | _(vide)_ | Mettre à `true`, `1` ou `yes` pour désactiver les opérations d'écriture |
| `DUPLICATI_DB_PATH` | _(vide)_ | Chemin vers `Duplicati-server.sqlite` — active les outils d'historique SQLite |
| `MCP_TRANSPORT` | `stdio` | Transport : `stdio` ou `streamable-http` |
| `MCP_PORT` | `3000` | Port pour le transport Streamable HTTP |

### Mode lecture seule

`DUPLICATI_READONLY=true` désactive `run_backup`, `abort_backup`, `update_backup_config` et `import_backup_config`. Tous les outils de lecture restent actifs. Utile pour explorer et analyser les configurations de sauvegarde sans risque de modification.

### Accès SQLite

La définition de `DUPLICATI_DB_PATH` active les outils `db_*`, qui lisent directement les bases de données SQLite de Duplicati. L'accès est strictement en lecture seule : les bases sont ouvertes en mode lecture seule et copiées en mémoire via l'API SQLite Online Backup avant toute requête — les bases Duplicati ne sont jamais verrouillées ni modifiées.

**Utilisation locale** — pointer vers la base serveur sur la machine :
```
DUPLICATI_DB_PATH=/chemin/vers/duplicati/config/Duplicati-server.sqlite
```

**Docker** — partager le répertoire de config Duplicati en volume lecture seule. Dans `docker-compose.yml` :

```yaml
services:
  duplicati-mcp:
    # ...
    volumes:
      - duplicati_config:/duplicati-config:ro   # volume nommé (recommandé)
      # ou : - /srv/duplicati/config:/duplicati-config:ro  # bind mount
    environment:
      - DUPLICATI_DB_PATH=/duplicati-config/Duplicati-server.sqlite

volumes:
  duplicati_config:   # doit être le même volume que celui utilisé par le conteneur Duplicati
```

## Docker Hub

- **Dépôt** : [kcofoni/duplicati-mcp](https://hub.docker.com/r/kcofoni/duplicati-mcp)
- **Tag latest** : `kcofoni/duplicati-mcp:latest`

```bash
docker pull kcofoni/duplicati-mcp:latest
```

## Développement

### Structure des fichiers

```
duplicati-mcp/
├── src/
│   └── duplicati_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── client.py        # Client REST API Duplicati
│       ├── db.py            # Accès SQLite lecture seule (DB serveur + DB par-backup)
│       └── server.py        # Serveur FastMCP et outils
├── mcp-publication/         # Fichiers de publication au registre MCP
├── requirements.txt         # Dépendances Python
├── pyproject.toml           # Métadonnées du projet
├── Dockerfile
├── docker-compose.yml
├── .mcp.json                # Config Claude Code locale (stdio)
├── test_server.sh           # Test de fumée du container Docker
├── test_mcp.py              # Test du protocole MCP
├── README.md                # Documentation anglaise
└── README_fr.md             # Ce fichier
```

### Lancer les tests

```bash
# Test de fumée (nécessite le container Docker en cours d'exécution)
./test_server.sh

# Test du protocole MCP (nécessite le serveur en cours d'exécution)
python test_mcp.py
python test_mcp.py localhost:3000
```

### Test interactif des outils (local)

```bash
uv run mcp dev src/duplicati_mcp/server.py
```

## Dépannage

### Impossible de se connecter à Duplicati

Vérifier que `DUPLICATI_URL` est accessible depuis le container. Si les deux tournent dans Docker, les mettre sur le même réseau et utiliser le nom de service comme hostname.

### Authentification échouée

Vérifier que `DUPLICATI_PASSWORD` correspond au mot de passe configuré dans l'interface web de Duplicati. Laisser vide si aucun mot de passe n'est configuré.

### L'endpoint MCP ne répond pas

```bash
docker ps | grep duplicati-mcp-server
docker logs duplicati-mcp-server
```

## Licence

Ce projet est sous licence MIT — voir le fichier [LICENSE](LICENSE) pour les détails.
