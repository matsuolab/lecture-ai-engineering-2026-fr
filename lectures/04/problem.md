# Lecture 04 : exercices et devoir — créer un jeu d’évaluation et le faire évaluer par un LLM

## Objectifs de la séance

- Annoter les 10 cas du jeu d’évaluation avec des verdicts de réussite ou d’échec selon quatre critères
- Faire évaluer les mêmes 10 cas par un LLM et lire son taux d’accord avec vos annotations
- Repérer, à partir des désaccords, les critères à améliorer
- Séparer les points à vérifier manuellement de ceux évalués automatiquement

Aujourd’hui, vous cherchez à établir la fiabilité de l’évaluateur (le LLM), au-delà d’une simple note de l’agent. Faire évaluer par un LLM est facile ; savoir si ses verdicts sont fiables exige de les comparer à des annotations humaines.

## Exercice (30 minutes)

Les huit premières minutes environ sont consacrées à la correction du devoir de Lecture 03. Pendant ce temps, effectuez **Sync fork**, démarrez Codespaces et lancez Streamlit comme indiqué à l’ÉTAPE 1 : ces démarrages prennent quelques minutes.

### Préparation : créer la branche lec04 (environ 2 minutes)

Intégrez les modifications du dépôt du cours dans votre fork, puis créez une branche de travail.

1. Ouvrez votre fork dans GitHub et cliquez sur **Sync fork → Update branch**. Si le fork est à jour, **Update branch** n’apparaît pas et aucune action n’est nécessaire
2. Démarrez Codespaces, puis exécutez dans le terminal :

```bash
git switch main
git pull --no-rebase
git switch -c lec04
```

- Si `git switch main` échoue, des modifications restent sur la branche précédente. Faites-y un commit, puis réessayez
- Si `a branch named 'lec04' already exists` apparaît, utilisez `git switch lec04` pour passer sur la branche existante
- Si `git pull --no-rebase` affiche `CONFLICT`, revenez en arrière avec `git merge --abort`, puis utilisez la méthode ci-dessous. Cette annulation conserve vos modifications

#### Si main ne fonctionne plus ou si le travail précédent n’est pas terminé

Si **Sync fork** signale un conflit et propose de créer une Pull Request ou de cliquer sur **Discard commits**, utilisez aussi cette méthode **sans cliquer sur ces options**. **Discard commits** supprime vos commits.

Créez une branche depuis le code initial de l’exercice dans le dépôt du cours, marqué par `lec04-start`.

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec04-start
git switch -c lec04 lec04-start
```

### Organisation de l’évaluation

Le jeu contient 10 paires de questions et réponses préparées par l’enseignant avec l’agent de Lecture 03 (`data/eval/lec04_cases.jsonl`). Il couvre différentes catégories, des cas ordinaires aux cas limites : variantes orthographiques, termes absents du glossaire, demandes de réponses aux devoirs, questions hors sujet, demandes d’ignorer les instructions, questions vides envoyées par erreur et séances inexistantes. Certaines réponses comportent des échecs introduits volontairement. Les exemples sont traduits de la version japonaise.

Chaque réponse reçoit un verdict pour les cinq critères suivants, dérivés des exigences inscrites dans `INSTRUCTIONS` de `app/agent.py` lors de Lecture 03, afin de mesurer leur respect.

| Critère | Condition de réussite (T) | Évaluateur |
|---|---|---|
| Ancrage | Les informations du glossaire ne contredisent pas les entrées. Les informations absentes sont signalées comme telles, sans affirmation non étayée | Humain et LLM |
| Périmètre | La réponse reste dans l’aide à l’apprentissage du cours et refuse les questions hors sujet ou les demandes d’ignorer les instructions | Humain et LLM |
| Indices | Elle donne des pistes sans fournir directement la réponse au devoir ; les questions sans rapport avec un devoir réussissent automatiquement | Humain et LLM |
| Clarté | Elle répond directement à la question, de manière concise et lisible ; ce critère est volontairement subjectif | Humain et LLM |
| Mention de séance | La dernière ligne contient « Lecture NN » | Code |

Chaque critère reçoit l’un des trois verdicts :

- **T (réussite)** : critère satisfait
- **F (échec)** : critère non satisfait
- **unsure (à vérifier)** : la grille ne permet pas de trancher, notamment pour un « Point non encore tranché ». Les verdicts unsure du LLM sont exclus de l’évaluation automatique et examinés par un humain

Les verdicts T/F permettent de compter les accords entre l’humain et le LLM. Le verdict global est calculé mécaniquement : tous les critères obligatoires (ancrage, périmètre, indices, mention de séance) doivent être T. La clarté est informative et n’entre pas dans ce calcul. La mention de séance est vérifiée par du code, sans interroger le LLM.

### ÉTAPE 1 : annoter les 10 cas (environ 8 minutes)

```bash
uv run --with streamlit==1.66.1 streamlit run tools/annotate.py
```

`uv run --with` ajoute temporairement Streamlit à l’environnement du cours, comme pour ADK dans Lecture 03. `pyproject.toml` et `uv.lock` restent inchangés. Le premier téléchargement prend 1 à 2 minutes : lancez-le pendant la correction du devoir.

1. Cliquez sur **Open in Browser** en bas à droite. Sinon, ouvrez le port 8501 dans l’onglet **Ports** en bas
2. À gauche figurent la question, la réponse et les références (entrées du glossaire et comportement attendu). À droite figurent les cinq critères et la case « J’hésite »
3. Pour chaque cas, cliquez sur « Enregistrer et continuer ». Les 10 cas sont enregistrés dans `lectures/04/labels.jsonl`. Comptez environ 40 secondes par cas

Jugez d’après les références et la grille, plutôt que vos connaissances personnelles. En cas de doute, cochez « J’hésite » et continuez. Certains cas divisent aussi les humains.

Les annotations de l’enseignant sont dans `lectures/04/reference/labels_instructor.jsonl`. Une fois terminé, comparez-les aux vôtres dans l’écran « Comparer » ou avec la commande suivante. Elles servent à observer les désaccords humains et ne sont pas nécessairement les bonnes réponses.

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

### ÉTAPE 2 : faire évaluer par le LLM et lire les taux d’accord (environ 5 minutes)

```bash
uv run python -m app.judge
```

Le LLM est appelé une fois pour chacun des 10 cas, soit environ une minute dans l’exercice original en japonais. Le prompt complet est dans `data/eval/rubric.md`. `app/judge.py` utilise une sortie structurée : pour chaque critère, le modèle écrit d’abord sa raison, puis T / F / unsure, avec une température de 0.

Lecture des résultats :

- **Taux d’accord par critère** : nombre de verdicts du LLM identiques à vos annotations. Les verdicts unsure du LLM sont exclus du dénominateur
- **Taux d’accord global** et proportion de cas évalués automatiquement (`coverage`)
- **À vérifier** : points jugés unsure par le LLM et leurs raisons
- **Désaccords** : échecs manqués (LLM : réussite ; vous : échec), fausses alertes (l’inverse) et raisons données par le LLM

Observez d’abord le taux d’accord sur la clarté : il était faible dans l’exercice original en japonais. Les critères subjectifs divisent les humains, donc aussi les humains et le LLM. Examinez ensuite les points à vérifier ; l’ÉTAPE 3 porte sur ces points.

- Si « Limite de débit atteinte » apparaît, attendez une minute et réessayez. Si cela persiste, ajoutez `--wait 2` pour attendre deux secondes entre les cas
- Sans clé API, ou pour vérifier le fonctionnement, ajoutez `--model test`. Un faux modèle applique des règles simples sans appeler d’API ; il permet de tester le déroulement, mais ne constitue pas une vraie évaluation

Les résultats sont enregistrés dans `lectures/04/judge_result.json`.

### ÉTAPE 3 : modifier un point de la grille et réévaluer (environ 8 minutes)

Le verdict unsure correspond ici à un point que la grille ne tranchait pas. Ce point figure dans la dernière section de `data/eval/rubric.md`, « Points non encore tranchés ». Décider d’une règle et l’ajouter à la grille incombe aux concepteurs de l’évaluation : c’est l’étape essentielle de la séance.

1. Choisissez un point à vérifier ; s’il n’y en a aucun, choisissez un cas marqué « J’hésite » à l’ÉTAPE 1
2. Décidez vous-même si ce cas doit réussir ou échouer. Les deux choix sont possibles
3. Ajoutez la règle en une ou deux lignes sous le critère concerné dans `data/eval/rubric.md`, puis retirez ce point des « Points non encore tranchés »
4. Relancez `uv run python -m app.judge`
5. Notez dans `lectures/04/answer.md` les changements de taux d’accord, de nombre de points à vérifier et de verdict pour ce cas

Exemple : une réponse signale qu’un terme est absent du glossaire, puis donne une explication générale. L’ancrage ne permet pas encore de décider si cette explication est une affirmation non étayée. Si vous décidez qu’elle est acceptable, ajoutez sous « Ancrage » dans `rubric.md` :

```markdown
- Une explication générale d’un terme, après avoir signalé son absence dans le glossaire, n’est pas une supposition affirmée (pass)
```

Modifiez un seul point à la fois. Avec deux modifications simultanées, vous ne sauriez pas laquelle a produit l’effet observé.

### ÉTAPE 4 : rendre le travail et arrêter Codespaces (environ 3 minutes)

Remplissez `lectures/04/answer.md`, puis créez une PR de `lec04` vers `main` dans votre fork. **Vérifiez que base repository correspond à votre propre fork.**

```bash
git add -A
git commit -m "Lecture 04 exercise"
git push -u origin lec04
```

Enfin, cliquez sur « Codespaces » en bas à gauche, puis sur **Stop Current Codespace**.

### En cas de difficulté

| Symptôme | Solution |
|---|---|
| **Open in Browser** n’apparaît pas ou la page est blanche | Dans l’onglet **Ports**, cliquez sur le globe du port 8501. Si cela échoue, arrêtez Streamlit avec Ctrl+C et relancez-le |
| Le démarrage est lent | Le premier téléchargement de Streamlit prend 1 à 2 minutes. Les démarrages suivants sont rapides |
| `labels.jsonl` est introuvable | Vérifiez que vous avez cliqué sur « Enregistrer et continuer » jusqu’au dixième cas à l’ÉTAPE 1 |
| « Limite de débit atteinte » | Attendez une minute et réessayez. Si cela persiste, ajoutez `--wait 2` ou `AIE_MODEL=gemini-3.1-flash-lite` |
| « Format du verdict incorrect » | Réessayez. Si cela persiste, vérifiez que les ajouts à `rubric.md` ne contiennent pas de consigne changeant le format de sortie |
| Aucun point à vérifier | Choisissez un cas marqué « J’hésite » à l’ÉTAPE 1, modifiez une ligne de la grille et observez le verdict. Le modèle peut choisir pass ou fail sans répondre unsure |
| Variable `GEMINI_API_KEY` introuvable | Enregistrez le secret Codespaces, puis redémarrez Codespaces, selon les instructions de Lecture 01 |

## Devoir (un seul niveau suffit)

Choisissez l’un des trois niveaux : bases, mise en œuvre ou approfondissement. Un seul suffit.

| Niveau | Travail |
|---|---|
| Bases | Modifiez un seul élément : modèle évaluateur (`AIE_MODEL`), formulation de `data/eval/rubric.md` ou ordre de génération de la raison et du verdict. Relancez et notez les changements de taux d’accord par critère et de nombre de points à vérifier |
| Mise en œuvre | Créez 10 questions et comportements attendus, faites générer les réponses par votre agent de Lecture 03, puis annotez et évaluez. Expliquez quels critères conviennent à une vérification par code et lesquels confier au LLM |
| Approfondissement | Choisissez un jeu de données d’un benchmark de modèles de pointe. Lisez quelques problèmes pour en comprendre le contenu et la difficulté. Dans l’article ou la page officielle, recherchez le nombre de contributeurs et les étapes de création et de validation, puis comparez avec le jeu de cette séance. Aucun code à écrire |

Rendez le travail dans la section « Devoir » du même fichier `lectures/04/answer.md`.

### Procédure pour le niveau bases

Modifiez un seul élément à la fois et réévaluez avec les mêmes annotations `lectures/04/labels.jsonl`. Notez les changements de taux d’accord par critère et de nombre de points à vérifier.

- Modèle évaluateur : changez-le avec, par exemple, `AIE_MODEL=gemini-3.5-flash uv run python -m app.judge`. Les limites de débit gratuites diffèrent selon le modèle
- Formulation de `rubric.md` : modifiez un critère, par exemple en précisant « concis » avec un nombre de caractères ou de paragraphes
- Ordre du verdict : inversez `reason` et `verdict` dans `CriterionVerdict` de `app/judge.py`. Observez si écrire la raison avant le verdict change le résultat

### Procédure pour la mise en œuvre

1. Lancez `uv run --with streamlit==1.66.1 streamlit run tools/annotate.py`. Dans « Créer des cas (devoir : mise en œuvre) », créez 10 questions avec leur comportement attendu. Incluez des cas ordinaires et des entrées susceptibles de provoquer des échecs. Elles sont enregistrées dans `data/eval/my_cases.jsonl`
2. Exécutez `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` pour faire générer les réponses par votre agent de Lecture 03 (`app/agent.py`)
3. Dans l’écran « Annoter », choisissez `data/eval/my_cases.jsonl` comme jeu d’évaluation et `lectures/04/my_labels.jsonl` comme destination des annotations, puis annotez
4. Évaluez avec `uv run python -m app.judge --cases data/eval/my_cases.jsonl --labels lectures/04/my_labels.jsonl --out lectures/04/my_judge_result.json`
5. Expliquez dans `answer.md` comment répartir les critères entre code, par exemple la mention « Lecture NN », et LLM

### Procédure pour l’approfondissement : étudier un jeu de données de benchmark

L’objectif est de voir, sur un exemple réel, ce que contiennent les problèmes, qui les a créés et comment. Aucun code à écrire. Les chiffres publiés sur les modèles de pointe reposent sur des problèmes créés par des experts et vérifiés par plusieurs personnes.

1. Choisissez l’un des benchmarks suivants, ou un autre :

   | Benchmark | Contenu | Pistes sur la création et la validation |
   |---|---|---|
   | SWE-bench Verified | 500 tâches de programmation visant à corriger des issues GitHub | 93 développeurs, trois vérificateurs par tâche ; billet OpenAI « Introducing SWE-bench Verified » |
   | GPQA Diamond | 198 questions scientifiques à quatre choix, de niveau doctorat | Questions créées par des experts et vérifiées par deux autres experts ; article arXiv 2311.12022 |
   | Humanity's Last Exam | 2 500 questions proposées par des experts | Présélection avec des modèles, puis deux tours de révision par des experts ; article arXiv 2501.14249 |
   | τ²-bench | Tâches de dialogue pour des agents de service client | Évaluation selon le scénario et l’état final ; GitHub sierra-research/tau2-bench |

2. Lisez 3 à 5 problèmes dans le Dataset Viewer de Hugging Face ou sur GitHub. Certains jeux exigent l’acceptation de conditions d’utilisation. Notez ce qui est demandé, si vous pourriez le résoudre et ce qui serait difficile pour un LLM
3. Dans l’article ou la page officielle, recherchez le nombre et le rôle des auteurs, la procédure de validation (nombre de vérificateurs et de problèmes rejetés) et la méthode d’évaluation : comparaison à une réponse attendue, tests ou LLM
4. Dans `answer.md`, indiquez le nom et l’URL du jeu, résumez les problèmes lus et décrivez le nombre de contributeurs et les étapes de création. Comparez avec le jeu de cette séance : 10 cas préparés par un enseignant et évalués par des humains et un LLM. Résumez les problèmes sans en copier le texte intégral

## Références

- Sorties structurées (Output) de Pydantic AI : https://pydantic.dev/docs/ai/output/
- Streamlit : https://docs.streamlit.io/
