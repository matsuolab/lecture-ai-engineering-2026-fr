# Lecture 06 : exercices et devoir — utiliser des outils via un serveur MCP

## Objectifs de la séance

- Extraire les outils de Lecture 03 dans un **serveur MCP** et les utiliser **via MCP** depuis le même agent
- Lire les noms, descriptions et arguments des outils visibles par le modèle
- Ajouter des outils externes prêts à l’emploi **en modifiant uniquement la configuration**

## Préparation

Si vous avez terminé le travail des séances précédentes, créez la branche `lec06` depuis `main`.
Cette séance ajoute des dépendances : exécutez une fois `uv sync --frozen`.

```bash
git switch main && git switch -c lec06
uv sync --frozen
```

Sinon, créez une branche depuis le code initial de l’exercice dans le dépôt du cours (tag `lec06-start`).

```bash
git remote -v                     # Si upstream manque, l’ajouter avec la ligne suivante
git remote add upstream https://github.com/matsuolab/lecture-ai-engineering-2026.git
git fetch upstream --tags
git switch -c lec06 lec06-start
uv sync --frozen
```

## Exercice (30 minutes)

### 1. Lister les outils visibles par le modèle

```bash
uv run python -m app.agent --list-tools          # Lecture 03 : fonctions enregistrées directement
uv run python -m app.agent --mcp --list-tools    # Lecture 06 : outils reçus du serveur MCP
```

Les deux commandes fonctionnent sans clé API, car elles n’appellent pas de LLM.
La seconde démarre comme sous-processus le serveur (`app/mcp_server.py`) décrit dans `app/mcp_servers.json`, puis affiche les noms, descriptions et arguments des outils exposés.

- Vérifiez que les noms portent le **préfixe « nom_du_serveur_ »**, par exemple `glossary_search_glossary`. Cela distingue les outils de même nom appartenant à des serveurs différents
- Les descriptions sont les docstrings de `app/tools.py`. **Pour le modèle, les fonctions outils et les outils MCP ont la même forme**

### 2. Utiliser MCP depuis l’agent

```bash
uv run python -m app.agent --mcp --trace "Quels sont les 3 niveaux de devoirs du cours AIE2026 ?"
```

Comparez les réponses, noms d’outils et nombres de `requests` avec Lecture 03 (sans `--mcp`).
En interne, `build_mcp_agent()` dans `app/agent.py` lit la configuration, démarre les serveurs et transmet les outils à l’agent.

### 3. Exposer un outil

À l’emplacement `TODO(Lecture 06 exercice)` de `app/mcp_server.py`, exposez aussi `get_lecture_summary` via MCP (une ligne, comme pour `search_glossary`).

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "Qu’apprend-on dans Lecture 02 ?"
uv run pytest -q
```

Vérifiez que `glossary_get_lecture_summary` apparaît avec `--list-tools` et qu’il est appelé avec `--trace`.
Si vous avez créé `make_quiz` dans Lecture 03, vous pouvez aussi l’exposer de la même manière.

### 4. Ajouter un outil externe prêt à l’emploi par configuration

Ajoutez à `app/mcp_servers.json` le **serveur fetch** public (qui récupère une page à une URL et la renvoie en Markdown). Aucun code à écrire.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "Résume le début de https://modelcontextprotocol.io/ en 3 lignes en français"
```

- Au premier démarrage, `uvx` télécharge le serveur : cela prend environ 10 secondes
- Si `fetch_fetch({'url': ...})` apparaît dans `--trace`, **le Codespace accède réellement à l’URL choisie par le modèle**. Avant d’ajouter un outil externe, comprenez sa destination et les données qu’il envoie
- `INSTRUCTIONS` est conçu pour le glossaire. Si une question contenant une URL ne déclenche pas fetch, ajoutez une ligne comme « Lorsqu’une URL est fournie, lire son contenu avec fetch » dans `INSTRUCTIONS`

### 5. Remise

Remplissez `lectures/06/answer.md` et ouvrez une PR de `lec06` vers `main` dans votre fork.

## Devoir (un seul niveau suffit)

| Niveau | Travail |
|---|---|
| Bases | Démarrez le serveur avec `uv run python -m app.mcp_server --http`, remplacez `glossary` dans la configuration par `{"url": "http://127.0.0.1:8000/mcp"}`, puis posez la même question. Notez les différences de démarrage, de processus et de ports entre stdio et Streamable HTTP. Modifiez aussi la docstring d’un outil et comparez les effets sur `--list-tools` et les appels |
| Mise en œuvre | Ajoutez `make_quiz` de Lecture 03 (ou un nouvel outil) au serveur MCP et ajoutez un test avec TestModel à `tests/test_mcp_server.py`. Vérifiez la plage des arguments (par exemple, renvoyer un message clair pour une séance inexistante) et observez avec `--trace` comment une erreur via MCP apparaît au modèle |
| Approfondissement | Utilisez le même serveur de glossaire depuis **Copilot Chat**, client MCP de VS Code (voir ci-dessous). Vérifiez qu’un seul serveur fonctionne avec plusieurs clients et comparez à l’agent (`app/agent.py`). Comparez le déroulement des appels d’outils : qui démarre le serveur, présence d’une validation humaine et affichage du résultat |

### Procédure pour l’approfondissement

Copilot Chat est un client MCP de VS Code. Avec `.vscode/mcp.json` dans le dépôt, les outils du serveur sont disponibles dans le mode **Agent** du Chat (le format utilise `servers`, contrairement à `mcpServers` dans `app/mcp_servers.json`. Les commandes s’exécutent dans le dossier de travail, à la racine du dépôt).

```json
{
  "servers": {
    "aie-glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    }
  }
}
```

1. Créez ce fichier dans VS Code de Codespaces. Cliquez sur **Start** au-dessus de `servers` (sinon, dans la palette de commandes, choisissez **MCP: List Servers** → `aie-glossary` → Start). Le serveur démarre dans le Codespace
2. Ouvrez Copilot Chat et choisissez le mode **Agent**. Vérifiez que la liste des outils (🔧) contient `search_glossary` de `aie-glossary` (et `get_lecture_summary` si vous avez terminé l’étape 3)
3. Demandez « Quels sont les 3 niveaux de devoirs d’AIE2026 ? ». Si une confirmation (**Continue**) précède l’exécution, autorisez-la, puis vérifiez que l’outil de glossaire est appelé et utilisé pour répondre
4. Dans `answer.md`, mettez côte à côte les appels affichés dans Chat et ceux de `uv run python -m app.agent --mcp --trace`
5. Vous pouvez inclure `.vscode/mcp.json` dans la PR (sans secret, comme une clé API)

- Le mode Agent et MCP fonctionnent avec Copilot Free. Les échanges de chat sont toutefois soumis à un plafond mensuel : limitez-vous à quelques essais
- Les offres Copilot gérées par une entreprise ou un établissement (Business / Enterprise) peuvent désactiver MCP selon la politique de l’organisation. Essayez avec un compte personnel

## Attention

- Un serveur MCP est un **programme qui exécute du code**. N’inscrivez pas de serveur de provenance inconnue dans la configuration
- Le serveur fetch accède aux URL choisies par le modèle. Ne lui fournissez pas d’URL internes à une entreprise ni contenant des données personnelles
- Plus d’outils signifie plus de descriptions transmises au modèle, donc plus de tokens par appel et un choix d’outil plus difficile. Avec `--list-tools`, surveillez le nombre d’outils transmis

## Références

- Site officiel de MCP : https://modelcontextprotocol.io/
- Client MCP de Pydantic AI : https://pydantic.dev/docs/ai/mcp/client/
- SDK Python de MCP (création d’un serveur) : https://github.com/modelcontextprotocol/python-sdk
- Serveurs MCP publics : https://github.com/modelcontextprotocol/servers
- Utilisation de serveurs MCP dans VS Code : https://code.visualstudio.com/docs/copilot/customization/mcp-servers
