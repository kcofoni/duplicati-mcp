# Guide de Publication du Serveur MCP

Ce guide explique comment publier le serveur MCP Duplicati sur le registre officiel MCP en ligne de commande avec l'outil `mcp-publisher`.

## Prérequis

Avant de publier, assurez-vous d'avoir :

1. **mcp-publisher** : L'outil officiel de publication MCP
   ```bash
   curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
   ```

2. **Compte GitHub** : Pour l'authentification de l'espace de noms (ex: `io.github.nomutilisateur/*`)
3. **Docker et Docker Hub** : Pour construire et publier l'image Docker
4. **server.json à jour** : Le fichier `server.json` doit être correctement configuré

## Étape 1 : Vérifier la configuration

Vérifier que [`mcp-publication/duplicati/server.json`](./duplicati/server.json) est bien configuré :

```bash
cat mcp-publication/duplicati/server.json
```

Champs clés à vérifier :
- `name` : doit être `io.github.kcofoni/duplicati-mcp`
- `version` : doit correspondre au tag de l'image Docker (ex: `0.1.0`)
- `repository.url` : URL de votre dépôt GitHub
- `packages[0].identifier` : image Docker avec le bon tag de version

S'authentifier sur Docker Hub avant de builder :

```bash
docker login
```

## Étape 2 : Builder et publier l'image Docker

Le registre MCP exige que les images supportent `linux/amd64`.

### Option A : Build simple (Linux AMD64)

```bash
docker build -t kcofoni/duplicati-mcp:v0.1.0 -t kcofoni/duplicati-mcp:latest .
docker push kcofoni/duplicati-mcp:v0.1.0
docker push kcofoni/duplicati-mcp:latest
```

### Option B : Build multi-architecture (Mac / ARM64)

```bash
# Configuration unique
docker buildx create --use --name multiarch

# Build et push pour linux/amd64 et linux/arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:v0.1.0 \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

> **Note** : Builder depuis un Mac sans buildx crée des images ARM64 uniquement, ce qui provoquera un échec de validation au registre MCP.

## Étape 3 : S'authentifier avec mcp-publisher

```bash
cd mcp-publication/duplicati
mcp-publisher login github
```

Suivre le flux OAuth GitHub.

## Étape 4 : Publier

```bash
mcp-publisher publish
```

L'outil valide `server.json`, authentifie l'espace de noms et soumet au registre.

## Étape 5 : Vérifier

En cas de succès :
```
✓ Successfully published io.github.kcofoni/duplicati-mcp@0.1.0
```

Le serveur sera trouvable sur https://registry.modelcontextprotocol.io.

## Mise à jour d'une publication existante

1. Mettre à jour `version` dans `server.json`
2. Builder et pousser la nouvelle image Docker avec le tag correspondant
3. Relancer `mcp-publisher publish`

## Dépannage

### Erreur "no child with platform linux/amd64"

Utiliser l'Option B (buildx) lors du build depuis un Mac.

### La publication échoue avec des erreurs de validation

```bash
# Valider le server.json
jq . mcp-publication/duplicati/server.json
```

Vérifier que l'image Docker existe et est publique sur Docker Hub.

## Ressources

- **Registre MCP** : https://github.com/modelcontextprotocol/registry
- **Schéma serveur** : https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
