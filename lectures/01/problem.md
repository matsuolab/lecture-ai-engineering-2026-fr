# Lecture 01 : exercices et devoir — préparer l’environnement et interroger un LLM

## Objectifs de la séance

- Ouvrir votre fork dans Codespaces et appeler Gemini API
- Modifier un peu de code avec GitHub Copilot
- Rendre le travail par une PR depuis une branche de travail (la même procédure servira aux séances suivantes)

## À préparer

- Un compte GitHub personnel (les comptes gérés par une entreprise peuvent être privés de Codespaces ou de Copilot par la configuration de l’organisation)
- Un compte Google personnel (les comptes Google Workspace professionnels peuvent être privés d’AI Studio par les paramètres d’administration)

## Exercice (45 minutes)

### 1. Créer un fork du dépôt du cours

Cliquez sur **Fork** en haut à droite du dépôt du cours pour créer un fork dans votre compte. Tout le travail suivant se fera dans votre fork.

### 2. Créer une clé Gemini API

Créez et copiez une clé API dans [Google AI Studio](https://aistudio.google.com/apikey).

> La clé API est secrète. Ne la collez pas dans le code, les chats ou les commits. En cas de fuite, supprimez-la dans AI Studio et créez-en une autre.

### 3. L’enregistrer comme secret Codespaces

Dans GitHub, choisissez **Settings → Codespaces → Secrets → New secret**, puis remplissez :

- Name : `GEMINI_API_KEY`
- Value : la clé de l’étape 2
- Repository access : sélectionnez **votre propre fork**

> Enregistrez le secret avant de démarrer Codespaces. S’il a été ajouté après le démarrage, redémarrez Codespaces.

### 4. Démarrer Codespaces

Dans votre fork, choisissez **Code → Codespaces → Create codespace on main**. La préparation initiale prend quelques minutes. Exécutez la commande suivante dans le terminal et vérifiez que les tests réussissent.

```bash
uv run pytest -q
```

### 5. Interroger le LLM sans outils

```bash
uv run python -m app.ask "Qu’est-ce que LoRA ?"
uv run python -m app.ask "Quels sont les 3 niveaux de devoirs du cours AIE2026 ?"
```

La première question porte sur un terme général et devrait recevoir une réponse globalement correcte. La seconde porte sur les « 3 niveaux de devoirs » propres au cours. Un LLM sans outils ne connaît pas le cours : il répondra qu’il ne sait pas, ou donnera une réponse plausible fondée sur des généralités. La bonne définition figure dans `data/glossary.json`, à l’entrée `homework-levels`. Comparez-la à la réponse du modèle.

Si vous avez le temps, essayez d’autres questions propres au cours. Observez que la réponse à une même question peut changer à chaque exécution et que le modèle peut répondre avec assurance à propos de ce qu’il ignore.

```bash
uv run python -m app.ask "Qu’est-ce que le tag lecNN-start utilisé dans le cours AIE2026 ?"
uv run python -m app.ask "Qu’apprend-on dans Lecture 02 du cours AIE2026 ?"
```

### 6. Afficher le nombre de tokens avec Copilot

Dans `app/ask.py`, à l’emplacement `TODO(Lecture 01 exercice)`, ajoutez l’affichage du nombre de tokens d’entrée et de sortie. Vous pouvez utiliser la complétion et le chat de Copilot. Lisez et comprenez le code proposé avant de l’adopter.

### 7. Créer une branche et une PR

```bash
git switch -c lec01
# Remplir lectures/01/answer.md
git add -A
git commit -m "Lecture 01 exercise"
git push -u origin lec01
```

Dans votre fork sur GitHub, créez une PR de `lec01` vers `main`. **Vérifiez que base repository correspond à votre propre fork** (n’envoyez pas de PR au dépôt du cours).

### 8. Arrêter Codespaces

Cliquez sur « Codespaces » en bas à gauche, puis sur **Stop Current Codespace**. Un Codespace laissé actif continue de consommer le quota gratuit.

## Devoir (un seul niveau suffit)

| Niveau | Travail |
|---|---|
| Bases | Posez chaque question trois fois, changez de modèle (variable d’environnement `AIE_MODEL`) ou de température (`temperature`), puis résumez les différences de réponses dans answer.md |
| Mise en œuvre | Modifiez `app/ask.py` pour pouvoir poser plusieurs questions de suite en conservant l’historique de conversation |
| Approfondissement | Mesurez le temps de réponse et le nombre de tokens pour plusieurs modèles ou questions. Réfléchissez aussi au lien avec les limites de débit de l’offre gratuite |

Exemple de changement de modèle :

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "Qu’est-ce que LoRA ?"
```

### Précisions sur le modèle appelé

Les spécifications des modèles peuvent évoluer.
La documentation de l’API Gemini a été mise à jour : Gemini 3.5 Flash est désormais déprécié et redirige vers Gemini 3.6 Flash.

- Référence : documentation de Gemini 3.5 Flash
https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash?hl=fr

Comme le montre cet exemple, les spécifications des LLM proposés sous forme de services changent fréquemment. Prenez l’habitude de consulter la documentation des services afin de vous adapter à ces évolutions.

Pour le devoir de Lecture 01, vous pouvez utiliser le modèle de votre choix.

Pour changer le paramètre `temperature`, consultez l’argument `config` de `generate_content`.
