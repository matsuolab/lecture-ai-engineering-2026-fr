# Lecture 03 : exercices et devoir — créer un agent d’aide à l’apprentissage

## Objectifs de cette séance

- Vérifier dans votre propre code qu’un agent se compose d’un « modèle + boucle + outils »
- Lire quels outils ont été appelés et avec quels arguments
- Ajouter un outil

## Exercices (30 minutes)

Les cinq premières minutes environ seront consacrées à l’explication du devoir de Lecture 02. Pendant ce temps, cliquez sur Sync fork à l’étape 1 et démarrez Codespaces (le démarrage prend quelques minutes).

### 1. Récupérer les mises à jour du dépôt du cours et créer la branche lec03

Intégrez les modifications du dépôt du cours à votre fork avant de créer une branche de travail.

1. Ouvrez votre fork sur GitHub et cliquez sur **Sync fork → Update branch** (si le fork est déjà à jour, Update branch n’apparaît pas et vous n’avez rien à faire)
2. Démarrez Codespaces et exécutez les commandes suivantes dans le terminal

```bash
git switch main
git pull --no-rebase
git switch -c lec03
```

- Si `git switch main` s’arrête, des modifications non validées restent sur la branche de la séance précédente. Faites un commit sur cette branche, puis réessayez
- Si `a branch named 'lec03' already exists` apparaît, vous avez déjà créé `lec03`. Basculez dessus avec `git switch lec03`
- Si `git pull --no-rebase` affiche `CONFLICT`, revenez à l’état précédent avec `git merge --abort`, puis utilisez la méthode ci-dessous (l’annulation de la fusion conserve vos modifications)

#### Si main ne fonctionne plus ou si le travail des séances précédentes n’est pas terminé

Si Sync fork signale un conflit et propose de créer une pull request ou de sélectionner « Discard commits », **ne cliquez pas sur ces options** et commencez avec la méthode ci-dessous. « Discard commits » supprime vos propres commits.

Créez une branche à partir du code de départ du dépôt du cours (le tag `lec03-start`).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec03-start
git switch -c lec03 lec03-start
```

### 2. Poser à l’agent la même question qu’en Lecture 01

```bash
uv run python -m app.agent "Quels sont les 3 niveaux de devoirs du cours AIE2026 ?"
```

Comparez la réponse à celle de `app.ask` en Lecture 01. L’agent consulte le glossaire avant de répondre. L’information correcte se trouve dans l’entrée `homework-levels` de `data/glossary.json`.

### 3. Lire les appels d’outils

```bash
uv run python -m app.agent --trace "Quelle est la différence entre LoRA et QLoRA ?"
```

Sur les lignes `[tool call]`, vérifiez quels outils le modèle a appelés et avec quels arguments. `requests` dans `[usage]` indique le nombre d’appels au LLM pour une question.

Les instructions au modèle expliquent pourquoi il faut chercher avant de répondre et consulter un seul terme à la fois. Elles se trouvent à deux endroits :

- `INSTRUCTIONS` dans `app/agent.py` (vers la ligne 31) : instructions générales de l’agent, telles que « consultez toujours le glossaire avec search_glossary » et « Terminez la réponse en indiquant les séances concernées (Lecture NN) »
- La docstring de chaque outil dans `app/tools.py` : transmise au modèle comme description de l’outil. Celle de `search_glossary` indique de mettre un seul terme à rechercher dans `query`

Pour le devoir de niveau Bases, vous modifierez ces instructions pour comparer les changements de comportement.

### 4. Écrire et enregistrer l’outil make_quiz

Permettez à l’agent de créer une question à partir du glossaire lorsqu’on lui demande une question de révision sur Lecture 02. Le modèle appelle `make_quiz` avec `lecture=2` ; l’outil choisit un terme de Lecture 02 et renvoie une question et sa réponse, que le modèle utilise pour poser la question.

1. Ajoutez la fonction `make_quiz(lecture: int) -> str` dans `app/tools.py`
2. Rédigez une docstring expliquant quand et pourquoi utiliser l’outil (le modèle la lit pour décider de l’utiliser ou non)
3. Récupérez dans le glossaire (`load_glossary()`) les termes dont le champ `lecture` correspond à la séance demandée et choisissez-en un (par exemple avec `random.choice`)
4. Renvoyez une chaîne contenant une question comme « Que signifie ce terme ? » et la réponse (la `definition` du terme), par exemple avec `json.dumps`
5. Enregistrez l’outil avec `agent.tool_plain(tools.make_quiz)` à l’emplacement `TODO(Lecture 03 exercice)` dans `app/agent.py`

Exemple de valeur renvoyée par `make_quiz(2)` :

```text
{"question": "Que signifie PEFT ?", "answer": "Plutôt que tous les paramètres du modèle, …"}
```

### 5. Vérifier que make_quiz est appelé

```bash
uv run python -m app.agent --list-tools    # Outils visibles par le modèle (sans clé API)
uv run python -m app.agent --trace "Pose-moi une question de révision sur Lecture 02"
uv run pytest -q
```

Si la liste contient `make_quiz` et votre docstring, et qu’une ligne comme `[tool call] make_quiz({'lecture': 2})` apparaît, vous avez réussi.

Sans utiliser de clé API, `uv run pytest -q` appelle tous les outils, y compris votre `make_quiz`, avec des arguments fictifs (comme `lecture=0`) pour vérifier qu’ils ne provoquent pas d’erreur. Lecture 0 n’existe pas : le test échoue donc si vous n’avez pas prévu le cas où aucun terme n’est trouvé. Dans ce cas, faites renvoyer un message clair par l’outil lorsqu’il n’y a pas de termes.

- Absent de la liste → il n’est pas enregistré dans `app/agent.py`
- Présent mais jamais appelé → décrivez un cas d’utilisation précis dans la docstring. Ajoutez à `INSTRUCTIONS` une consigne comme « Utilisez make_quiz lorsqu’une question de révision est demandée »

### 6. Rendre le travail et arrêter Codespaces

Remplissez `lectures/03/answer.md` et créez une PR de `lec03` vers `main` dans votre propre fork. **Vérifiez que base repository correspond à votre propre fork.**

```bash
git add -A
git commit -m "Lecture 03 exercise"
git push -u origin lec03
```

Si vous n’avez pas terminé l’étape 4, vous pouvez rendre vos résultats jusqu’à l’étape 3. Poussez la suite du travail sur la même branche pour mettre à jour la PR.

Enfin, cliquez sur « Codespaces » en bas à gauche → **Stop Current Codespace**.

## Devoir (un seul niveau suffit)

Choisissez l’un des trois niveaux : Bases, Mise en œuvre ou Approfondissement. Il suffit de travailler sur l’un d’eux pour terminer le devoir.

| Niveau | Travail |
|---|---|
| Bases | Modifiez `INSTRUCTIONS` dans `app/agent.py` ou les docstrings des outils dans `app/tools.py`, vus pendant les exercices. Posez la même question avec `--trace`, puis comparez et notez les changements dans les appels d’outils et les réponses |
| Mise en œuvre | Créez l’outil `save_learning_log` pour enregistrer des notes d’apprentissage dans `learning_log/`. L’enregistrement étant une opération difficile à annuler, demandez une confirmation à l’utilisateur avant de l’effectuer (`requires_approval=True` de Pydantic AI) |
| Approfondissement | Choisissez une option : (a) Conservez les mêmes instructions et outils que l’agent des exercices, réécrivez seulement son assemblage avec ADK de Google, exécutez-le avec `adk run`, puis comparez le code et les réponses. (b) Exécutez l’agent de programmation Pi dans Codespaces et comparez son prompt système public aux `INSTRUCTIONS` de votre agent |

Rendez votre travail dans la section « Devoir » du même `lectures/03/answer.md` que pour les exercices.

### Comment aborder le niveau Bases

Modifiez un seul des deux emplacements vus à l’étape 3 à la fois. Posez la même question avec `--trace` et comparez les résultats.

- `INSTRUCTIONS` dans `app/agent.py` (vers la ligne 31) : instructions générales de l’agent
- La docstring de chaque outil dans `app/tools.py` : transmise au modèle comme description de l’outil

Voici quelques modifications possibles. Notez comment changent les outils appelés, le nombre d’appels, les arguments et les réponses.

- Si vous supprimez de `INSTRUCTIONS` la consigne de toujours consulter le glossaire avec `search_glossary`, l’agent répond-il sans rechercher ?
- Si vous remplacez « Mettez un seul terme à rechercher dans query » par « Mettez plusieurs termes ensemble » dans la docstring de `search_glossary`, comment changent le nombre de recherches et les arguments ?
- Si vous remplacez « Terminez la réponse en indiquant les séances concernées (Lecture NN) » dans `INSTRUCTIONS` par une autre consigne (par exemple « Terminez par une question de révision »), comment change la réponse ?

### Comment aborder le niveau Mise en œuvre

1. Créez `save_learning_log` dans `app/tools.py` et enregistrez-le dans `app/agent.py` avec `requires_approval=True`
2. Lorsque le modèle appelle cet outil, l’exécution s’arrête en attente d’approbation et renvoie `DeferredToolRequests` comme résultat (`result.output`). Ajoutez donc `DeferredToolRequests` à `output_type` de l’agent (sinon une erreur se produit)

   ```python
   from pydantic_ai import Agent, DeferredToolRequests

   agent = Agent(instructions=INSTRUCTIONS,
                 output_type=[str, DeferredToolRequests])
   ```

3. Dans la CLI, demandez à l’utilisateur si l’enregistrement est autorisé pour chaque appel de `result.output.approvals`. Passez ces décisions (`DeferredToolResults`) et la conversation jusqu’à ce moment (`message_history=result.all_messages()`) à un nouvel appel à `run_sync`

Pour plus de détails, consultez Human-in-the-Loop Tool Approval dans la documentation officielle Pydantic AI « Deferred Tools » : https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/

### Comment aborder l’option d’approfondissement (a) : réécrire avec ADK

Conservez les instructions et les outils de l’agent des exercices, et réécrivez uniquement son assemblage avec ADK.

| Périmètre | Contenu |
|---|---|
| Réutiliser | `INSTRUCTIONS` de `app/agent.py`, ainsi que `search_glossary` et `get_lecture_summary` de `app/tools.py` (et `make_quiz` si vous l’avez créé pendant les exercices) |
| Écrire | Créez `agent.py` (le code ci-dessous) et `__init__.py` (contenant uniquement `from . import agent`) dans `adk_agent/glossary_agent/` |
| Non requis | Les fonctions de commande comme `--trace`, les tests ou les outils soumis à approbation. Ne modifiez pas les fichiers dans `app/` |
| Comparer | Le code (comment transmettre les instructions et les outils) et les réponses aux mêmes questions que pendant les exercices |

Structure de `adk_agent/glossary_agent/agent.py` :

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[...],  # Outils utilisés pendant les exercices
)
```

Exécutez la commande suivante depuis la racine du dépôt :

```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

- `adk run` permet de dialoguer dans le terminal. Saisissez une question et appuyez sur Enter pour obtenir une réponse. Pour terminer, saisissez `exit`
- `uv run --with google-adk` ajoute temporairement ADK à l’environnement du cours pour cette exécution. Cela ne modifie ni `pyproject.toml` ni `uv.lock`
- `PYTHONPATH=.` permet d’importer le dossier `app` depuis la racine du dépôt
- La clé API provient du secret Codespaces `GEMINI_API_KEY` déjà configuré
- Le premier téléchargement d’ADK prend environ une minute

Posez les mêmes questions que pendant les exercices, puis notez les différences de code et de réponses par rapport à la version Pydantic AI.

ADK 2.0 a introduit des changements importants. Certains articles sur le web peuvent contenir des informations anciennes qui n’en tiennent pas compte ; suivre la documentation officielle aide à éviter les erreurs d’implémentation.

- Documentation officielle : https://adk.dev/

### Comment aborder l’option d’approfondissement (b) : exécuter Pi dans Codespaces

Pi est un agent de programmation qui modifie des fichiers et exécute des commandes sans demander confirmation. Essayez-le dans Codespaces plutôt que sur votre propre PC.

1. **Installer** : exécutez la commande suivante dans le terminal Codespaces

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. **Démarrer** : saisissez `pi` dans le terminal
3. **Configurer le modèle** : dans Pi, saisissez `/model` et choisissez un modèle Gemini. La clé API provient du secret Codespaces `GEMINI_API_KEY` existant
4. **Comparer** : le prompt système de Pi se trouve dans `packages/coding-agent/src/core/system-prompt.ts` du dépôt public https://github.com/earendil-works/pi. Comparez-le à vos `INSTRUCTIONS` pour voir ce qui est inclus ou omis

- Documentation officielle de Pi : https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## Références

- Pydantic AI: https://pydantic.dev/docs/ai/
- ADK: https://adk.dev/
