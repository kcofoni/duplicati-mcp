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

## Configuration client (Docker/distant)

### Claude Code

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

**macOS** : `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows** : `%APPDATA%\Claude\claude_desktop_config.json`

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
8. **import_backup_config** — Importer une configuration de job depuis un JSON

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DUPLICATI_URL` | `http://localhost:8200` | URL de l'instance Duplicati |
| `DUPLICATI_PASSWORD` | _(vide)_ | Mot de passe de l'interface web Duplicati (laisser vide si aucun) |
| `DUPLICATI_READONLY` | _(vide)_ | Mettre à `true`, `1` ou `yes` pour désactiver les opérations d'écriture |
| `MCP_TRANSPORT` | `stdio` | Transport : `stdio` ou `streamable-http` |
| `MCP_PORT` | `3000` | Port pour le transport Streamable HTTP |

### Mode lecture seule

`DUPLICATI_READONLY=true` désactive `run_backup`, `abort_backup` et `import_backup_config`. Tous les outils de lecture restent actifs. Utile pour explorer et analyser les configurations de sauvegarde sans risque de modification.

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
