# Guide de Publication du Serveur MCP

Ce guide couvre la publication du serveur MCP Duplicati sur les trois registres : **PyPI**, **Docker Hub** et le **registre officiel MCP**.

---

## Partie 1 — PyPI

### Prérequis

- Un compte PyPI sur https://pypi.org
- Un compte TestPyPI sur https://test.pypi.org (même compte, inscription séparée)
- Des tokens API pour les deux (créés dans les paramètres du compte)

### Configuration

Le `pyproject.toml` contient déjà la configuration de l'index TestPyPI :

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

Ce bloc indique à `uv publish --index testpypi` où uploader.

### Étape 1 : Builder le package

```bash
uv build
```

Génère deux fichiers dans `dist/` :
- `duplicati_mcp-X.Y.Z-py3-none-any.whl` — wheel (binaire installable)
- `duplicati_mcp-X.Y.Z.tar.gz` — source distribution (contient le README affiché sur PyPI)

> **Important** : Toujours rebuilder avant de publier si `README.md` ou un fichier source a changé — c'est le README à l'intérieur du `.tar.gz` qui s'affiche sur la page du package PyPI.

### Étape 2 : Dry-run (optionnel)

```bash
uv publish --index testpypi --dry-run
```

Liste les fichiers qui seraient uploadés sans les envoyer.

### Étape 3 : Publier sur TestPyPI

```bash
UV_PUBLISH_TOKEN="votre-token-testpypi" uv publish --index testpypi
```

> **Note sur les tokens** : PyPI propose des tokens scopés à un projet (valides uniquement pour un projet existant) et des tokens scopés au compte (valides pour tout projet y compris les nouveaux). Pour une **première publication**, utiliser un token de compte — le projet n'existant pas encore, un token de projet retourne une erreur 403.

Vérifier sur https://test.pypi.org/project/duplicati-mcp/

Tester l'installation :
```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  duplicati-mcp
```
(`--extra-index-url` est nécessaire car les dépendances comme `mcp` ne sont pas sur TestPyPI.)

### Étape 4 : Publier sur PyPI (production)

Une fois TestPyPI validé :

```bash
UV_PUBLISH_TOKEN="votre-token-pypi" uv publish
```

Vérifier sur https://pypi.org/project/duplicati-mcp/

Tester avec uvx :
```bash
uvx duplicati-mcp@latest
```

### Mise à jour d'une version existante

Bumper `version` dans `pyproject.toml`, rebuilder, puis republier. PyPI n'autorise pas l'écrasement d'une version existante.

---

## Partie 2 — Docker Hub

### Prérequis

- Compte Docker Hub
- Connecté : `docker login`
- buildx configuré (builds Mac / multi-architecture)

### Étape 1 : Configuration buildx unique (Mac uniquement)

```bash
docker buildx create --use --name multiarch
```

### Étape 2 : Builder et pousser l'image multi-architecture

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:vX.Y.Z \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

> **Note** : Le registre MCP exige `linux/amd64`. Builder depuis un Mac sans buildx crée des images ARM64 uniquement et échouera à la validation du registre.

Vérifier que l'image est publique sur https://hub.docker.com/r/kcofoni/duplicati-mcp

---

## Partie 3 — Registre officiel MCP

### Prérequis

- Image Docker déjà publiée sur Docker Hub (Partie 2 obligatoirement faite avant)
- `mcp-publisher` installé :
  ```bash
  curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
  ```
- `server.json` mis à jour avec la version et le tag Docker corrects

### Étape 1 : Vérifier server.json

```bash
cat mcp-publication/duplicati/server.json
```

Champs clés à vérifier :
- `version` : doit correspondre au tag de l'image Docker (ex: `1.0.0`)
- `packages[0].identifier` : `docker.io/kcofoni/duplicati-mcp:vX.Y.Z`

Valider le JSON :
```bash
jq . mcp-publication/duplicati/server.json
```

### Étape 2 : S'authentifier

```bash
cd mcp-publication/duplicati
mcp-publisher login github
```

Suivre le flux OAuth GitHub. Requis une seule fois ; le token est mis en cache localement.

### Étape 3 : Publier

```bash
mcp-publisher publish
```

En cas de succès :
```
✓ Successfully published io.github.kcofoni/duplicati-mcp@X.Y.Z
```

Vérifier sur https://registry.modelcontextprotocol.io (rechercher "duplicati").

### Mise à jour d'une publication existante

1. Mettre à jour `version` dans `server.json`
2. Builder et pousser la nouvelle image Docker (Partie 2)
3. Relancer `mcp-publisher publish`

### Dépannage

**Erreur "no child with platform linux/amd64"** : utiliser buildx (Étape 2 de la Partie 2).

**403 sur mcp-publisher** : vérifier que l'image Docker est bien publique sur Docker Hub avant de publier.

---

## Ressources

- **PyPI** : https://pypi.org/project/duplicati-mcp/
- **TestPyPI** : https://test.pypi.org/project/duplicati-mcp/
- **Docker Hub** : https://hub.docker.com/r/kcofoni/duplicati-mcp
- **Registre MCP** : https://registry.modelcontextprotocol.io
- **Schéma serveur** : https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
