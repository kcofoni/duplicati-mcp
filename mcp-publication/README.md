# MCP Publication Files / Fichiers de Publication MCP

This directory contains the files and documentation for publishing the Duplicati MCP server to the official MCP registry.

Ce répertoire contient les fichiers et la documentation pour publier le serveur MCP Duplicati sur le registre officiel MCP.

## Contents / Contenu

### Configuration Files / Fichiers de Configuration

- **[`duplicati/server.json`](duplicati/server.json)** - MCP server definition file conforming to the official schema / Fichier de définition du serveur MCP conforme au schéma officiel

### Documentation / Documentation

- **[`PUBLICATION_GUIDE.md`](PUBLICATION_GUIDE.md)** - English guide for publishing the server using `mcp-publisher`
- **[`GUIDE_PUBLICATION.md`](GUIDE_PUBLICATION.md)** - Guide en français pour publier le serveur avec `mcp-publisher`

## Quick Start / Démarrage Rapide

### English

1. Install `mcp-publisher`:
   ```bash
   curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
   ```

2. Ensure your Docker image is published to Docker Hub

3. Navigate to the server.json directory and publish:
   ```bash
   cd mcp-publication/duplicati
   mcp-publisher publish
   ```

For detailed instructions, see [PUBLICATION_GUIDE.md](PUBLICATION_GUIDE.md).

### Français

1. Installer `mcp-publisher` :
   ```bash
   curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
   ```

2. S'assurer que l'image Docker est publiée sur Docker Hub

3. Naviguer vers le répertoire server.json et publier :
   ```bash
   cd mcp-publication/duplicati
   mcp-publisher publish
   ```

Pour des instructions détaillées, voir [GUIDE_PUBLICATION.md](GUIDE_PUBLICATION.md).

## Schema Version / Version du Schéma

Current schema: `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`

## Resources / Ressources

- **MCP Registry**: https://github.com/modelcontextprotocol/registry
- **MCP Documentation**: https://modelcontextprotocol.io/
