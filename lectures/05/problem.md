# Lecture 05 : exercices et devoir — répondre en recherchant dans les documents de cours

La base de recherche fournie couvre 214 pages des cours principaux de Lecture 01 à Lecture 03. Elle reprend les vecteurs de la source japonaise et renvoie le texte traduit. Le contexte complet contient actuellement 6 documents et 342 pages. La présentation d’accueil et les exercices de Lecture 01 et 02 restent à intégrer.

## Objectifs de la séance

- Exécuter des réponses à partir de tous les documents ou d’une recherche, puis comparer les réponses, leurs sources, le temps et le nombre de tokens
- Expliquer la représentation des données avec un fragment par page et les différences entre recherche vectorielle, Tree et Graph
- Améliorer la récupération des documents pour votre usage et comparer avant et après avec la même question

Nous reprenons la structure « modèle + boucle + outils » de Lecture 03 en changeant la manière de récupérer les documents de cours. En vous appuyant sur l’évaluation de Lecture 04, vérifiez vous-même la justesse des réponses et les éléments justificatifs des pages citées.

## Documents et code utilisés

| Fichier | Contenu |
|---|---|
| [data/rag_data/lectures.json](../../data/rag_data/lectures.json) | Titres et textes par cours, chapitre et page. Une page correspond à un fragment |
| [data/rag_data/tree.json](../../data/rag_data/tree.json) | Hiérarchie des documents, chapitres et pages |
| [data/rag_data/graph.json](../../data/rag_data/graph.json) | Nœuds représentant notamment les pages et termes, et relations entre eux |
| [data/rag_data/index.sqlite3](../../data/rag_data/index.sqlite3) | Base de recherche contenant les 214 pages des cours principaux de Lecture 01 à Lecture 03 |
| [scripts/build_rag_index.py](../../scripts/build_rag_index.py) | Création des embeddings et de la base SQLite de recherche |
| [app/retrieval.py](../../app/retrieval.py) | Recherche vectorielle, parcours Tree et Graph, et envoi de tous les documents |
| [app/tools.py](../../app/tools.py) | Descriptions, entrées et sorties des outils accessibles au modèle |
| [app/agent.py](../../app/agent.py) | Instructions, enregistrement des outils et choix du mode d’exécution |
| [app/config.py](../../app/config.py) | Documents concernés, nombre de résultats, étendue du parcours Graph et autres réglages |

**Périmètre actuel** : la recherche vectorielle, Tree et Graph utilisent les 214 pages des cours principaux de Lecture 01 à Lecture 03. Le mode de contexte complet fournit les 6 documents et les 342 pages figurant dans le JSON de cette version. Cet exercice observe les différentes voies de récupération. Pour comparer équitablement les méthodes, commencez par leur donner le même ensemble de documents.

## Préparation

### 1. Intégrer la mise à jour de Lecture 05 et créer la branche lec05

Dans votre fork, sélectionnez **Sync fork → Update branch** pour mettre à jour `main`. Ouvrez le terminal de Codespaces, puis exécutez les commandes ci-dessous pour créer votre branche de travail.

```bash
git switch main
git pull --no-rebase
git switch -c lec05
uv sync --frozen
```

- Si `lec05` existe déjà, utilisez `git switch lec05`
- Si des modifications de la séance précédente empêchent le changement de branche, faites un commit sur cette branche, puis réessayez
- En cas de conflit pendant la mise à jour, consultez l’enseignant sans abandonner vos modifications

La clé API utilise la même variable `GEMINI_API_KEY` que dans Lecture 01. Si vous ajoutez le secret après le démarrage de Codespaces, redémarrez Codespaces. Consultez le [README](../../README.md) pour la configuration.

### 2. Vérifier la base de recherche fournie

La recherche vectorielle et Graph utilisent directement `data/rag_data/index.sqlite3`. Après intégration de la mise à jour de Lecture 05, passez à l’exercice. L’embedding des questions et la génération des réponses utilisent `GEMINI_API_KEY`. Tree et le contexte complet n’ont pas besoin de cette base.

## Exercice

### ÉTAPE 1 : fournir tous les documents en une fois

Dans le même terminal, définissez d’abord la question de comparaison dans une variable. Réutilisez exactement cette question pour chaque méthode ci-dessous.

```bash
AIE_QUESTION='Selon Lecture 02, que fige LoRA et qu’entraîne-t-il ? Qu’ajoute QLoRA ?'
uv run python -m app.agent --full-context --trace "$AIE_QUESTION"
```

Notez la réponse, les pages citées et les valeurs finales `[time]`, `[usage]` et `[cost]` dans [answer.md](answer.md).

Le contexte complet peut aussi produire une réponse correcte. Observez le résultat réel sans présumer un échec. Distinguez une erreur de dépassement de la limite d’entrée d’un cas où l’entrée a été acceptée mais où le modèle n’a pas su utiliser les éléments nécessaires.

### ÉTAPE 2 : examiner uniquement les résultats de recherche

```bash
uv run python -m app.retrieval "LoRA QLoRA différence"
```

Sans utiliser l’agent, cette commande récupère au plus 5 pages proches de la question. Elle affiche le cours, le chapitre, le titre de page, le numéro de page du PDF et le texte.

- Trouvez-vous des pages qui étayent la réponse, par exemple `lec02-main-p052` ?
- Savez-vous distinguer les pages contenant simplement des termes similaires de celles qui justifient la réponse ?

Ouvrez le JSON des documents dans l’éditeur et recherchez, par exemple, `lec02-main-p052` pour consulter le texte de cette page.

### ÉTAPE 3 : répondre à partir des résultats de recherche

```bash
uv run python -m app.agent --trace "$AIE_QUESTION"
```

Par défaut, l’agent dispose de `search_materials(query)`. Le modèle choisit les termes de recherche et répond à partir des textes renvoyés.

- Dans `[tool call]`, examinez les termes de recherche et le nombre d’appels d’outils
- Vérifiez que chaque référence étaye l’explication. Elle indique la page traduite vérifiée ou la page japonaise qui a servi de source à la traduction.
- Distinguez les cas où les éléments nécessaires n’ont pas été récupérés de ceux où ils ont été récupérés mais mal utilisés

Pour certaines questions, la page 52 suffit à réunir tous les éléments nécessaires. Augmenter le nombre de pages citées n’est pas un objectif en soi.

### ÉTAPE 4 : poser la même question avec Tree et Graph

Tree choisit les pages en parcourant la table des matières.

```bash
uv run python -m app.agent --tree --trace "$AIE_QUESTION"
```

Ce mode utilise uniquement `browse_tree(node_id)`. Il obtient d’abord la liste des cours, puis parcourt cours, chapitres et pages avec les ID renvoyés. Les pages de `children` ne contiennent que leur première phrase. En spécifiant un ID de page, son texte complet apparaît dans `node.content`. Pour une page sans ponctuation de fin de phrase, le texte candidat est la première ligne. Dans la trace, examinez les rubriques choisies et les pages dont le texte complet a été récupéré.

Graph trouve ses points de départ par recherche vectorielle, puis élargit les candidats autour d’eux.

```bash
uv run python -m app.agent --graph --trace "$AIE_QUESTION"
```

Ce mode utilise `search_graph(query)`. À partir des 3 premiers résultats, il suit les relations entre pages voisines et termes communs sur au plus 2 sauts (`hop`) et renvoie le texte de 10 pages au maximum, points de départ compris. Passer d’une page à sa voisine compte pour 1 saut ; passer d’une page à une autre via un terme compte pour 2 sauts. Un terme commun ne garantit pas la présence de la réponse.

Notez comment Tree et Graph modifient la réponse, les sources citées, le temps et le nombre de tokens d’entrée.

### ÉTAPE 5 : comparer et consigner les résultats

Rassemblez les résultats de chaque méthode dans le tableau d’`answer.md`.

| Affichage | Signification |
|---|---|
| `[time]` | Secondes jusqu’à la fin de la réponse, recherche et embeddings inclus |
| `[usage]` | Total des tokens d’entrée et de sortie et des réponses du modèle pour une question |
| `[cost]` | Coût estimé de l’API de génération, hors embedding de la requête et construction de l’index |

Si le coût est « non calculable », notez-le ainsi sans le traiter comme zéro.

Si vous avez le temps, répétez la comparaison avec d’autres questions. Conservez des résultats distincts pour chaque question.

| Type | Exemple de question | Sources à vérifier |
|---|---|---|
| Plusieurs pages | Dans les exemples de Lecture 03, quelle différence entre la compaction du contexte et la mémoire entre sessions ? Toutes les notes quotidiennes vont-elles dans la mémoire à long terme ? | `lec03-main-p013`, `lec03-main-p039`, `lec03-main-p040` |
| Information absente | Quels sont le temps de réponse moyen mesuré et le taux de réponses correctes du RAG que nous venons de créer ? | Les documents de cours ne contiennent aucun journal de mesures de ce système |

### ÉTAPE 6 : rendre le travail et arrêter Codespaces

Notez les résultats dans `lectures/05/answer.md`, puis ouvrez une PR de votre branche de travail vers `main` dans votre fork. **Vérifiez que base repository correspond à votre propre fork.**

```bash
git add lectures/05/answer.md
# Si vous avez modifié du code, ajoutez aussi les fichiers concernés avec git add
git commit -m "Lecture 05 exercices et devoir"
git push -u origin lec05
```

Excluez des commits les clés API et les bases de recherche expérimentales. Enfin, choisissez **Stop Current Codespace** dans « Codespaces » en bas à gauche.

## Devoir (un seul niveau suffit)

Choisissez bases, mise en œuvre ou approfondissement. **Un seul niveau suffit.** Dans la section « Devoir » du même `answer.md`, indiquez le niveau, le travail réalisé, les résultats, vos observations et vos questions.

| Niveau | Travail |
|---|---|
| Bases | Modifiez un seul élément parmi les instructions, la description d’un outil ou le nombre de résultats. Exécutez la même question avec `--trace` et comparez avant et après |
| Mise en œuvre | Améliorez une opération de récupération, par exemple en ajoutant le texte des pages voisines aux résultats, puis comparez avec la recherche ordinaire |
| Approfondissement | Améliorez Tree, Graph ou leur combinaison. Définissez une question à résoudre et comparez avec le RAG de base sur cette même question |

### Procédure pour le niveau bases

Modifiez un seul endroit à la fois parmi :

- `INSTRUCTIONS` dans `app/agent.py`, ou respectivement `TREE_INSTRUCTIONS` et `GRAPH_INSTRUCTIONS` pour Tree et Graph
- La docstring d’un outil dans `app/tools.py`
- `RAG_TOP_K` dans `app/config.py`, qui définit le nombre de résultats de la recherche vectorielle ordinaire

Conservez la même question, le même modèle et les mêmes documents. Comparez les outils appelés, leurs arguments et le nombre d’appels, ainsi que les réponses et les sources citées. Notez aussi le temps, les tokens et le coût estimé de l’API de génération. Ces modifications seules ne nécessitent pas de reconstruire l’index.

### Procédure pour la mise en œuvre

Par exemple, modifiez `app/retrieval.py` pour renvoyer aussi le texte de la page précédente et de la page suivante.

1. Avec les informations de `load_pages()`, recherchez les pages voisines dans le même `document_id` que le résultat
2. Évitez les doublons et renvoyez ensemble le texte et les références de citation
3. Exécutez la même question qu’avant et repérez un cas où des éléments utiles ont été ajoutés et un cas où les informations inutiles ont augmenté
4. Notez l’implémentation, les comparaisons et les échecs restants

Vous pouvez choisir une autre amélioration de la récupération adaptée à votre usage. Modifier seulement l’étendue des documents récupérés, sans changer les textes ni la configuration des embeddings, ne nécessite pas de reconstruire l’index.

Si vous modifiez les textes ou les réglages d’embedding, suivez les [instructions du README](../../README.md#lecture-05-rag) : indiquez une base expérimentale avec `AIE_RAG_DB`, puis construisez l’index.

### Procédure pour l’approfondissement

1. Choisissez la question à résoudre, par exemple une explication couvrant plusieurs chapitres ou une comparaison de termes liés. Identifiez d’abord les pages qui étayent la réponse
2. Concevez la méthode de récupération : contenu de la table des matières et des textes candidats dans Tree, types de relations, nombre de sauts et choix des candidats dans Graph, ou combinaison de méthodes
3. Expliquez la structure, le stockage et la recherche des données, avec les raisons de vos choix
4. Comparez avec le RAG de base sur les mêmes question, modèle et documents. Notez les réponses, les sources citées, le temps, les tokens et le coût estimé de l’API de génération
5. Présentez des cas améliorés et des échecs, puis déterminez si vous adopteriez cette méthode pour votre usage

Vous pouvez utiliser des outils d’IA. Décrivez ce que vous avez exécuté et vérifié vous-même. Suivez les annonces du cours pour la date limite.

## En cas de difficulté

| Symptôme | À vérifier |
|---|---|
| `GEMINI_API_KEY` introuvable | Le secret Codespaces est-il enregistré ? Si vous l’avez ajouté après le démarrage, avez-vous redémarré Codespaces ? |
| « Base de recherche introuvable » | Intégrez la mise à jour de Lecture 05 et vérifiez la présence de `data/rag_data/index.sqlite3`. Si `AIE_RAG_DB` est défini, vérifiez le chemin indiqué |
| Limite de débit de l’API atteinte | Attendez selon le message affiché, puis réessayez |
| La question est vide | Si vous utilisez un nouveau terminal, définissez à nouveau `AIE_QUESTION` |
| Les résultats ne répondent pas à la question | Essayez uniquement la recherche avec `app.retrieval` et vérifiez les termes, les documents concernés et le nombre de résultats |
| Le contexte complet dépasse la limite d’entrée | Notez l’erreur et les conditions d’exécution, puis essayez une autre méthode. Signalez les essais non exécutés dans le tableau |

Les résultats peuvent varier pour une même question. Ne concluez pas à la supériorité d’une méthode sur un seul succès ou échec : examinez les éléments récupérés et ceux réellement utilisés.
