# AIE2026 : dépôt des exercices et des devoirs

Ce dépôt sert aux exercices et aux devoirs du cours AI Engineering Pilot Course (AIE2026).
Tout au long du cours, vous développerez progressivement un **agent qui vous aide à apprendre l’ingénierie de l’IA**.

## Environnement prévu

Les exercices sont conçus pour être réalisés **avec un navigateur uniquement**. Aucune installation sur votre PC n’est nécessaire.

| Outil | Utilisation | Points à retenir |
|---|---|---|
| Compte GitHub **personnel** | Créer un fork de ce dépôt et rendre le travail avec une branche de travail et une PR | Les comptes gérés par une entreprise ou un établissement peuvent restreindre Codespaces et Copilot |
| GitHub Codespaces | Environnement de développement pour Lecture 01, Lecture 03, Lecture 05, etc. La configuration `.devcontainer/` prépare automatiquement un conteneur avec Python 3.12, uv et Node.js | Le quota gratuit d’un compte personnel est de 120 heures-cœur par mois (environ 60 heures avec 2 cœurs). **Arrêtez le Codespace après utilisation** |
| GitHub Copilot (Free suffit) | Complétion de code et chat. Sert aussi de client MCP dans le devoir d’approfondissement de Lecture 06 | Free impose un plafond mensuel pour les complétions et le chat |
| Gemini API (offre gratuite de Google AI Studio) | Appeler le LLM. Créez une clé avec un compte Google **personnel** et transmettez-la via le secret Codespaces `GEMINI_API_KEY` | L’offre gratuite impose des limites par minute et par jour (voir « Hypothèses et contraintes ») |
| Google Colab (GPU T4, offre gratuite) | Uniquement pour l’entraînement LoRA de Lecture 02 | La durée d’utilisation du GPU est limitée. Supprimez l’environnement d’exécution à la fin |

Pour travailler sur votre PC, installez Python 3.12 et [uv](https://docs.astral.sh/uv/), exécutez `uv sync --frozen`, puis définissez la variable d’environnement `GEMINI_API_KEY`.

## Pour commencer (Lecture 01)

1. Créez un **fork** de ce dépôt dans votre compte
2. Créez une clé Gemini API dans [Google AI Studio](https://aistudio.google.com/apikey)
3. Dans GitHub, ajoutez `GEMINI_API_KEY` sous **Settings → Codespaces → Secrets** et sélectionnez votre fork parmi les dépôts autorisés
4. Dans votre fork, choisissez **Code → Codespaces → Create codespace on main**
5. Vérifiez le fonctionnement dans le terminal

```bash
uv run pytest -q
uv run python -m app.ask "Qu’est-ce que LoRA ?"
```

Consultez [les instructions détaillées : lectures/01/problem.md](lectures/01/problem.md).

## Structure

```
.devcontainer/   Définition de l’environnement Codespaces (Python 3.12, uv, Node.js ; uv sync --frozen au démarrage)
.github/workflows/test.yml  Tests à chaque PR (à activer dans l’onglet Actions du fork)
app/
  config.py      Lecture du nom du modèle et de la clé API
  ask.py         Lecture 01 : poser une question au LLM
  tools.py       Lecture 03 : outils de l’agent (recherche dans le glossaire, etc.)
  agent.py       Lecture 03 : agent d’aide à l’apprentissage avec Pydantic AI (Lecture 06 : via MCP avec --mcp)
  judge.py       Lecture 04 : faire évaluer un jeu de cas par un LLM et mesurer l’accord avec les annotations humaines
  mcp_server.py  Lecture 06 : serveur MCP qui expose le glossaire
  mcp_servers.json Lecture 06 : configuration des serveurs MCP à utiliser (format mcpServers)
data/
  glossary.json  Glossaire du cours
  lectures/      Points essentiels de chaque séance
  eval/          Lecture 04 : jeu d’évaluation (lec04_cases.jsonl) et grille d’évaluation (rubric.md)
tools/
  annotate.py    Lecture 04 : interface d’annotation (Streamlit, ajouté temporairement avec uv run --with)
.streamlit/      Configuration Streamlit (accès par le transfert de ports Codespaces)
lectures/NN/
  problem.md     Exercices et devoirs de la séance
  answer.md      Fichier à remplir et à rendre
notebooks/       Lecture 02 : notebook LoRA à exécuter dans Google Colab (lora_format_tuning.ipynb)
scripts/         Scripts auxiliaires
tests/           Tests (sans clé API)
pyproject.toml / uv.lock  Dépendances et versions verrouillées
```

## Rendre le travail

1. Créez une branche de travail pour chaque séance (exemple : `git switch -c lec01`)
2. Réalisez les exercices et le devoir, puis remplissez `lectures/NN/answer.md`
3. Faites un push et créez une PR de la branche de travail vers `main`, **dans votre propre fork**

Chaque devoir propose trois niveaux : « bases », « mise en œuvre » et « approfondissement ». Il suffit d’en réaliser un.

## Hypothèses et contraintes

- **Les versions des dépendances sont verrouillées** (`uv.lock` : Python 3.12, pydantic-ai-slim 2.57.0, google-genai 2.31.0). Elles ne seront pas mises à jour pendant le cours. Installez-les telles quelles avec `uv sync --frozen`.
- **Le modèle par défaut est `gemini-3.5-flash-lite`**. Vous pouvez le changer avec la variable d’environnement `AIE_MODEL` (voir « Changer de modèle »). Vous pouvez aussi utiliser d’autres modèles ou une API souscrite à titre personnel
- **L’offre gratuite de Gemini API impose des limites de débit**. L’agent (à partir de Lecture 03) appelle plusieurs fois le LLM pour une question et atteint donc les limites plus vite que dans Lecture 01. Si le message `Limite de débit atteinte` apparaît, attendez environ une minute. Si `Le modèle est saturé (503)` persiste, essayez `AIE_MODEL=gemini-3.1-flash-lite`
- **Transmettez la clé API uniquement via la variable d’environnement `GEMINI_API_KEY`**. Ne la collez pas dans le code, les commits ou un chat. En cas de fuite, supprimez-la dans AI Studio et créez-en une autre
- Codespaces peut accéder à Internet, mais les connexions entrantes vers Codespaces sont bloquées (le transfert de ports est privé par défaut). Le serveur MCP de Lecture 06 fonctionne à l’intérieur de Codespaces
- Les tests (`uv run pytest -q`) fonctionnent sans clé API (ils utilisent TestModel, qui n’appelle pas de LLM)

## Règles à respecter

- **N’écrivez pas de clé API dans le code ou les commits.** Utilisez un secret Codespaces
- **Arrêtez Codespaces après utilisation.** Si vous épuisez le quota gratuit, vous ne pourrez plus le démarrer
- Vous pouvez utiliser des outils d’IA comme Copilot. Lisez et comprenez le code proposé avant de l’adopter

## Changer de modèle

Le modèle par défaut est `gemini-3.5-flash-lite`. Vous pouvez le changer avec la variable d’environnement `AIE_MODEL`.

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "Qu’est-ce que LoRA ?"
```

L’offre gratuite limite le nombre de requêtes par minute et par jour. Consultez [les limites de débit de Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits).
