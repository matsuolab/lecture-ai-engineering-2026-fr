# Exercices et devoir du cours 06 — Utiliser les outils d’un serveur MCP depuis un agent

## Objectifs de la séance

- Utiliser depuis un agent votre propre serveur MCP avec l’outil de glossaire du cours 03.
- Afficher et lire les noms, les descriptions et les arguments des outils transmis au modèle.
- Utiliser des serveurs MCP fournis par d’autres personnes en les ajoutant à un fichier de configuration.

Faites les exercices dans GitHub Codespaces à partir de votre fork. Utilisez la clé de l’API Gemini enregistrée au cours 01.

## Trois façons d’utiliser un serveur MCP

Essayez les trois configurations dans cet ordre.

| | Lancer son propre serveur | Utiliser un serveur publié | Se connecter à un serveur distant |
|---|---|---|---|
| Connexion | L’agent lance le serveur par une commande dans votre environnement | `uvx` télécharge et lance le serveur dans votre environnement | L’agent se connecte à un serveur qui fonctionne déjà |
| Exercice | STEP 1 et 2 (serveur du glossaire) | STEP 3 (serveur fetch) | STEP 4 (serveur AWS Knowledge) |
| Configuration | `"command": "uv"` | `"command": "uvx"` | `"url": "https://…"` |

Le champ `command` permet de lancer un serveur dans votre environnement. Le champ `url` sert à joindre un serveur distant.

## Fichiers du cours 06

Modifiez le fichier de configuration pendant l’exercice. Selon leur rôle, consultez ou exécutez les autres fichiers.

| Fichier | Rôle | Action |
|---|---|---|
| [app/tools.py](../../app/tools.py) | Contient les fonctions, dont `search_glossary` et `get_lecture_summary` du cours 03 | Consultez-le |
| [app/mcp_server.py](../../app/mcp_server.py) | Expose les fonctions de `app/tools.py` comme outils MCP | Consultez-le. Vous ajouterez une ligne dans le devoir de base |
| [app/mcp_servers.json](../../app/mcp_servers.json) | Configure les serveurs MCP utilisés par l’agent | Ajoutez des serveurs à STEP 3 et STEP 4 |
| [app/mcp_agent.py](../../app/mcp_agent.py) | Se connecte aux serveurs configurés et utilise leurs outils | Exécutez-le dans le terminal |
| [app/agent.py](../../app/agent.py) | Agent utilisé jusqu’au cours 05 | Exécutez-le à STEP 1 pour afficher ses outils |

## Exercices (30 minutes)

Comptez environ 23 minutes pour la préparation et les étapes STEP 1 à STEP 5.

### Préparation — Créer la branche lec06 (environ 2 minutes)

1. Sur la page GitHub de votre fork, sélectionnez **Sync fork → Update branch** si une mise à jour est proposée.
2. Dans le terminal de Codespaces, exécutez ces commandes dans l’ordre.

```bash
git switch main
git pull --no-rebase
git switch -c lec06
uv sync --frozen
```

3. Exécutez `ls app/mcp_agent.py` et vérifiez que le nom du fichier s’affiche.

- Si `git switch main` s’arrête à cause de modifications sur la branche de la séance précédente, faites un commit de votre travail et réessayez.
- Si vous voyez `a branch named 'lec06' already exists`, passez sur cette branche avec `git switch lec06`.
- Si `git pull --no-rebase` signale `CONFLICT`, utilisez `git merge --abort` pour conserver vos modifications, puis suivez les instructions ci-dessous.

#### Si le travail d’une séance précédente est encore en cours

Partez du code actuel du cours 06 dans le dépôt du cours. Exécutez les commandes dans l’ordre.

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026-fr.git main
git switch -c lec06 FETCH_HEAD
uv sync --frozen
```

Utilisez aussi cette méthode si Sync fork signale un conflit. Pour conserver vos commits, laissez l’option **Discard commits** de côté.

### STEP 1 — Afficher les outils de votre serveur (environ 4 minutes)

Vérifiez que l’agent lance le serveur du glossaire et transmet ses outils au modèle.

```bash
uv run python -m app.agent --list-tools
uv run python -m app.mcp_agent --list-tools
```

Les deux commandes fonctionnent sans clé API.

1. La première liste les outils de l’agent utilisé jusqu’au cours 05, dont `search_materials`.
2. La première ligne de la seconde commande indique comment l’agent a lancé le serveur du glossaire. Les outils du serveur apparaissent en dessous.
3. Comparez les listes. Le modèle reçoit les noms, les descriptions et les arguments sous la même forme.

La seconde commande affiche le résultat suivant.

```text
[server] glossary: lancement par la commande (uv run python -m app.mcp_server)
Outils visibles par le modèle : 1

[glossary_search_glossary]
  Rechercher un terme dans le glossaire du cours et renvoyer sa définition et la séance associée.

  Utiliser cet outil avant de répondre sur un terme d’ingénierie de l’IA ou une expression propre
  au cours AIE2026. Mettre un seul terme à rechercher dans query (exemple : "LoRA").
  Arguments: {"query": {"title": "Query", "type": "string"}}
```

Le nom d’un outil MCP se compose du nom du serveur, d’un trait de soulignement et du nom de l’outil. Dans `glossary_search_glossary`, `glossary` vient de la configuration et `search_glossary` est la fonction de `app/tools.py`. Le préfixe distingue les outils portant le même nom sur des serveurs différents.

### STEP 2 — Poser une question à l’agent et examiner l’appel d’outil (environ 4 minutes)

Vérifiez que l’agent utilise l’outil du serveur MCP pour répondre à une question.

```bash
uv run python -m app.mcp_agent --trace "Quels sont les 3 niveaux de devoirs dans le cours AIE2026 ?"
```

La question est la même qu’au cours 03. Examinez ces lignes après `--- trace ---`.

1. `[tool call]` affiche `glossary_search_glossary` et les arguments choisis par le modèle.
2. `[tool return]` affiche le contenu du glossaire renvoyé par le serveur MCP.
3. `[usage]` indique au moins deux réponses du modèle. Il appelle l’outil dans la première réponse, puis lit le résultat et répond dans la suivante.

Au cours 03, l’agent appelait directement la fonction. Ici, le serveur MCP appelle la fonction et renvoie son résultat à l’agent.

### STEP 3 — Télécharger et utiliser un serveur publié (environ 5 minutes)

Ajoutez fetch, un serveur qui récupère des pages web, et vérifiez que l’agent peut l’utiliser.

1. Ouvrez `app/mcp_servers.json`. Ajoutez une virgule après l’accolade fermante de `glossary`, puis les quatre lignes de `"fetch"`.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
    }
  }
}
```

2. Exécutez la première commande. Repérez `[server] fetch: lancement par la commande` et `fetch_fetch` dans la liste.
3. Posez la question avec la seconde commande. Repérez `fetch_fetch` et son URL sur la ligne `[tool call]`.

```bash
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "Résumez le début de https://modelcontextprotocol.io/ en trois lignes en français."
```

- `uvx` télécharge et exécute un programme publié. Le serveur fetch tourne dans votre Codespace. La première commande prend une dizaine de secondes au premier lancement.
- `==2026.11.11` fixe la version pour éviter les changements de comportement dus aux mises à jour d’un serveur externe.
- `--no-readability-js` demande au serveur d’extraire le contenu de la page uniquement avec Python.
- Le modèle reçoit la description de `fetch_fetch` en anglais, telle que l’auteur du serveur l’a écrite.

### STEP 4 — Se connecter à un serveur distant (environ 5 minutes)

Connectez-vous par URL au serveur MCP hébergé par AWS et vérifiez que l’agent peut l’utiliser.

1. Ouvrez `app/mcp_servers.json`. Ajoutez une virgule après l’accolade fermante de `fetch`, puis la ligne de `"aws"`.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
    },
    "aws": {"url": "https://knowledge-mcp.global.api.aws"}
  }
}
```

2. Exécutez la première commande. Repérez `[server] aws: connexion à l’URL` et les outils dont le nom commence par `aws_`.
3. Posez la question avec la seconde commande. Repérez un outil `aws_` sur la ligne `[tool call]`.

```bash
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "Cherchez dans la documentation AWS et expliquez en deux lignes la gestion des versions d’Amazon S3."
```

La première commande commence par ces trois lignes.

```text
[server] glossary: lancement par la commande (uv run python -m app.mcp_server)
[server] fetch: lancement par la commande (uvx mcp-server-fetch==2026.11.11 --no-readability-js)
[server] aws: connexion à l’URL (https://knowledge-mcp.global.api.aws)
```

Le serveur tourne déjà chez AWS. L’agent se connecte directement à son URL et la question est envoyée à AWS.

### Vérifications avant d’ajouter des outils externes

Aux étapes STEP 3 et STEP 4, quelques lignes de configuration vous ont permis d’utiliser des serveurs d’autres fournisseurs. Faites d’abord ces deux vérifications.

1. **Qui fournit le serveur ?** Identifiez le fournisseur et l’emplacement du code source. Le dépôt de MCP fournit fetch. AWS fournit AWS Knowledge. Ajoutez les serveurs dont vous pouvez vérifier la provenance.
2. **Quels risques sont documentés ?** Lisez les avertissements et les paramètres par défaut dans le README ou sur le site officiel. Le README de fetch décrit le risque de sécurité lié à l’accès à des adresses IP internes. Les données transmises à un outil hébergé à distance sont envoyées au fournisseur.

Les réglages par défaut de fetch protègent les ressources internes et respectent les règles des sites sur la collecte automatisée.

| Réglage par défaut | Option |
|---|---|
| Ignore les adresses privées comme `localhost` et les réseaux internes | `--allow-private-ips` autorise leur accès |
| Ignore les pages dont le site interdit la récupération automatisée dans `robots.txt` | `--ignore-robots-txt` permet d’y accéder |
| Récupère les autres pages quel que soit l’hôte | `--allowed-hosts` limite les hôtes accessibles |

Consultez le fournisseur et les risques documentés avant d’ajouter un serveur, y compris ceux proposés dans le dépôt de MCP.

### STEP 5 — Rendre le travail et arrêter Codespaces (environ 3 minutes)

Notez vos résultats dans `answer.md`, ouvrez une PR et arrêtez le Codespace.

1. Ouvrez `lectures/06/answer.md`. Copiez le nom d’outil de STEP 1 et les lignes `[tool call]` de STEP 2 à STEP 4, avec les noms et les arguments affichés.
2. Faites un commit et un push.

```bash
git add -A
git commit -m "Exercices du cours 06"
git push -u origin lec06
```

3. Dans GitHub, ouvrez une PR de `lec06` vers `main` dans votre fork. Vérifiez que le dépôt de base est bien votre fork.
4. En bas à gauche, sélectionnez **Codespaces**, puis **Stop Current Codespace**.

Voici un exemple à reporter dans `answer.md`.

```text
- Nom de l’outil à STEP 1 — glossary_search_glossary
- STEP 2 [tool call] — glossary_search_glossary({'query': '3 niveaux'})
- STEP 3 [tool call] — fetch_fetch({'url': 'https://…'})
- STEP 4 [tool call] — aws_… (Copiez la ligne telle qu’elle s’affiche)
```

Si STEP 4 est inachevée, remettez les résultats obtenus et poussez la suite sur la même branche.

### Dépannage

Si le problème persiste, indiquez le symptôme et le message affiché dans le chat.

| Symptôme | Action |
|---|---|
| `No module named app.mcp_agent` | Mettez `main` à jour comme indiqué dans la préparation. Exécutez `git switch lec06`, puis `git merge main` |
| « Impossible de lire app/mcp_servers.json » | Vérifiez les virgules entre les serveurs près de la ligne indiquée et retirez toute virgule après le dernier serveur |
| « Impossible de se connecter à un serveur MCP » | Vérifiez la commande ou l’URL dans `app/mcp_servers.json` |
| fetch est ignoré pour une question contenant une URL | Ajoutez une ligne dans `INSTRUCTIONS` dans `app/mcp_agent.py` demandant d’utiliser fetch pour lire l’URL fournie |
| La connexion échoue après l’ajout de `aws` | Vérifiez l’URL. En cas de limite de requêtes, attendez environ une minute et réessayez |
| Limite de requêtes atteinte | Attendez environ une minute et relancez la commande |
| `GEMINI_API_KEY` est introuvable | Enregistrez la clé comme secret Codespaces comme au cours 01, puis redémarrez Codespaces |

## Devoir (choisir un niveau)

| Niveau | Travail |
|---|---|
| Bases | Exposez `get_lecture_summary` sur le serveur du glossaire en modifiant `app/mcp_server.py`. Conservez l’agent tel quel. Vérifiez que l’outil figure dans la liste et qu’il est appelé quand vous posez une question |
| Mise en œuvre | Ajoutez votre outil `make_quiz` du cours 03 ou créez-en un. Renvoyez un message clair en cas d’argument hors des valeurs attendues et observez ce que le modèle reçoit |
| Approfondissement | Consultez la documentation officielle d’un logiciel que vous utilisez, comme Claude Code, Codex ou Gemini CLI, pour voir comment configurer MCP. À défaut, choisissez VS Code. Comparez sa configuration avec `app/mcp_servers.json` |

### Devoir de base

| Composant | Fichier |
|---|---|
| Serveur | Modifiez `app/mcp_server.py`, qui détermine les outils exposés |
| Agent | Conservez `app/mcp_servers.json` et `app/mcp_agent.py` tels quels |

1. Ouvrez `app/mcp_server.py`. Ajoutez la dernière ligne de l’exemple sous le commentaire `TODO`, puis enregistrez.

   ```python
   server.tool()(tools.search_glossary)

   # TODO(Devoir de base) : exposer aussi get_lecture_summary
   server.tool()(tools.get_lecture_summary)
   ```

2. Exécutez `git status`. Une fois le travail de STEP 5 enregistré dans un commit, seul `app/mcp_server.py` doit apparaître comme modifié.
3. Vérifiez que `glossary_get_lecture_summary` figure dans la liste des outils.
4. Demandez ce que l’on apprend au cours 02 et vérifiez que le nouvel outil est appelé.
5. Exécutez `uv run pytest -q` et vérifiez que les tests réussissent.

```bash
git status
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "Qu’allons-nous apprendre au cours 02 ?"
uv run pytest -q
```

Au démarrage, l’agent demande au serveur sa liste d’outils. Il découvre ainsi l’outil ajouté.

### Devoir de mise en œuvre

1. Exposez `make_quiz` du cours 03 dans `app/mcp_server.py`, comme dans le devoir de base. Pour créer un outil, définissez une fonction dans ce fichier et placez `@server.tool()` juste au-dessus.
2. Utilisez `return` pour renvoyer un message clair si un argument est hors des valeurs attendues, par exemple un numéro de cours inexistant.
3. Posez une question qui produit un argument hors des valeurs attendues et observez `--trace`.

```bash
uv run python -m app.mcp_agent --trace "Crée un quiz sur le cours 99."
```

- Le message renvoyé par `return` figure sur la ligne `[tool return]` et arrive au modèle.
- Une exception provoquée par `raise` figure sur la ligne `[tool error]`. Comparez ce que le modèle reçoit dans les deux cas.

### Devoir d’approfondissement

1. Choisissez un logiciel que vous utilisez déjà, comme Claude Code, Codex ou Gemini CLI. À défaut, choisissez VS Code. Ce travail se fait à partir de la documentation.
2. Cherchez comment configurer ses serveurs MCP dans la documentation officielle.
3. Comparez cette méthode avec `app/mcp_servers.json` et notez les différences.

| Question | À vérifier |
|---|---|
| Où écrire la configuration ? | Nom et emplacement du fichier, ou commande d’enregistrement |
| Comment lancer un serveur par une commande ? | L’équivalent de `"command"` |
| Comment se connecter par URL ? | L’équivalent de `"url"` |
| Où la configuration s’applique-t-elle ? | Dans un seul projet ou dans tous |

Notez la date de consultation et l’URL de la documentation officielle. Les modalités de configuration peuvent évoluer.

### Rendre le devoir

Dans la section Devoir de `lectures/06/answer.md`, notez le niveau choisi, le travail effectué, les résultats et vos constats ou questions. Poussez vos modifications sur la même branche `lec06`. Vous pouvez utiliser des outils d’IA. Indiquez ce que vous avez vérifié vous-même.

## Références

- [Site officiel de MCP](https://modelcontextprotocol.io/)
- [Client MCP de Pydantic AI](https://pydantic.dev/docs/ai/mcp/client/)
- [SDK Python de MCP pour écrire des serveurs](https://github.com/modelcontextprotocol/python-sdk)
- [Serveurs MCP publics](https://github.com/modelcontextprotocol/servers)
- [README du serveur fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- [Serveur MCP AWS Knowledge](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server)
- [Utiliser des serveurs MCP dans VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
