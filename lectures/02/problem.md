# Lecture 02 : exercices et devoir — apprendre un format de réponse avec LoRA et comparer avant et après

Cette séance se déroule dans Google Colab (GPU T4, offre gratuite). Codespaces n’est pas utilisé.

## Objectifs de la séance

- Entraîner rapidement un petit modèle avec LoRA et vérifier, chiffres et sorties à l’appui, **ce qui change et ce qui ne change pas**
- Expliquer à partir de vos résultats que l’apprentissage du format ne garantit pas le bon jugement face à l’inconnu (demander une vérification ou affirmer une réponse)
- Expliquer avec vos propres mots les situations où l’ajustement fin convient ou non

## Notebook utilisé

- [Notebook LoRA : notebooks/lora_format_tuning.ipynb](../../notebooks/lora_format_tuning.ipynb)
- Ouvrir dans Colab : https://colab.research.google.com/github/matsuolab/lecture-ai-engineering-2026-fr/blob/main/notebooks/lora_format_tuning.ipynb

À partir d’une FAQ de cours fictive de 5 entrées, entraînez `Qwen/Qwen3.5-0.8B` avec LoRA pendant 20 époques (20 passages sur 14 exemples, soit 40 étapes ; 4 à 5 minutes sur T4 dans l’exercice original en japonais).
La sortie souhaitée est une ligne JSON `{"answer": ..., "needs_review": ...}`. Pour une question absente de la FAQ, la bonne réponse indique qu’une vérification est nécessaire, avec `needs_review: true`.
L’évaluation distingue le **taux de respect du format** (format JSON respecté) du **taux de réponses au contenu correct** (`needs_review` et expressions de la réponse conformes à la référence).

## Préparation facultative (5 minutes)

Avant le cours, exécuter les sections 0 à 3 du notebook permet de vérifier l’attribution d’un GPU, l’installation des bibliothèques et le téléchargement du modèle, et de réduire les difficultés le jour même.
Les variables de Colab disparaissent lorsque la session est interrompue : le jour du cours, recommencez à la section 0.

## Exercice (30 minutes)

1. Ouvrez le notebook dans Colab et créez votre copie avec **File → Save a copy in Drive**
2. Choisissez **Runtime → Change runtime type → T4 GPU**
3. Exécutez les sections 0 à 3 dans l’ordre (environ 5 minutes). Dans le tableau avant entraînement, repérez **les clés manquantes** et vérifiez si le texte correspond à la FAQ
4. Lancez l’entraînement en section 4 (4 à 5 minutes dans l’exercice original en japonais ; la durée peut varier avec les données françaises). Pendant l’attente, lisez « Différences entre LoRA et QLoRA ». Examinez `trainable%` et l’évolution de `Training Loss` (valeur de la fonction de perte)
5. Évaluez le modèle entraîné en sections 5 et 6, puis comparez avec les résultats précédents
   - Tableau comparatif : comment `format_rate` et `content_rate` ont-ils changé ?
   - `Régressions` : questions réussies avant l’entraînement mais échouées après (une liste vide est souhaitable ; examinez les régressions de votre propre exécution)
   - Types d’échecs restants : le modèle a-t-il **affirmé** une réponse en utilisant une autre entrée de la FAQ pour une question sans preuve, ou **évité de répondre** à une question couverte par la FAQ en déclarant qu’aucune information n’était disponible ?
   - Section 6 : pour les questions absentes de la FAQ et de l’entraînement, a-t-il demandé une vérification ou affirmé une réponse ?
6. Créez `result.json` en section 7. Notez les points essentiels dans `lectures/02/answer.md` et ouvrez une PR de la branche `lec02` vers `main` dans votre fork (vous pouvez modifier answer.md dans l’interface GitHub). Vous pouvez placer `result.json` dans `lectures/02/` et l’inclure dans la PR
7. Choisissez **Runtime → Disconnect and delete runtime**

> Le temps d’utilisation gratuit des GPU Colab est limité. Supprimez toujours l’environnement d’exécution à la fin.
> Si aucun GPU n’est disponible ou si l’entraînement ne se termine pas à temps, suivez la section 4b du notebook pour comparer et analyser les résultats obtenus par l’enseignant sur T4 avec l’exercice original en japonais. Pour la remise, réglez `executed_training_myself` sur `False` et indiquez dans answer.md les parties exécutées vous-même.

Même avec une graine aléatoire (`seed`) fixe, l’entraînement sur GPU n’est pas parfaitement reproductible. Il est normal que les questions encore échouées diffèrent entre participants : comparez les types d’échecs.

## Devoir (un seul niveau suffit)

| Niveau | Travail |
|---|---|
| Bases | Modifiez un seul paramètre de `CONFIG` parmi `lora_r`, `lr` et `num_train_epochs`, puis réentraînez. Comparez `format_rate`, `content_rate`, la valeur finale de la fonction de perte et la durée avec les réglages d’origine. Après modification, choisissez **Runtime → Restart session**, puis recommencez en haut (le modèle entraîné est encore en mémoire). Comparez deux fichiers `result.json` |
| Mise en œuvre | Remplacez `FAQ`, `GROUNDED` et `UNGROUNDED` par votre propre sujet (environ 5 entrées), entraînez et comparez avant et après. Conservez le format JSON et la conception de `needs_review`. Expliquez aussi comment vous avez préparé les questions sans preuve |
| Approfondissement | Avec `scripts/make_sft_dataset.py`, créez des paires Q&R à partir du glossaire (JSONL au format `messages`), puis entraînez le modèle sur ces données à la place de la FAQ. Préparez vos questions d’évaluation (termes présents, questions reformulées et termes absents) et les réponses attendues, puis comparez avant et après. Comparez avec un mécanisme de recherche dans le glossaire et examinez les avantages et les inconvénients de l’entraînement du modèle |

Création des données d’approfondissement (dans Codespaces, puis téléversement du fichier dans Colab) :

```bash
uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl
```

Dans Colab, chaque ligne possède le même format `messages` que `to_chat` dans le notebook. Transmettez directement les lignes lues à `Dataset.from_list` pour les utiliser avec le `SFTTrainer` de la section 4. Recréez vous-même les évaluations (`test` et `gold`) pour le glossaire.

La section 8 (chargement sur 4 bits et comparaison des sorties) est une observation sans entraînement : vous pouvez joindre ses résultats à n’importe quel niveau. L’entraînement sur 4 bits (QLoRA) n’a pas été vérifié dans l’environnement du cours (T4) et ne fait donc pas partie du devoir.

## Attention

- Après l’entraînement, un adaptateur est aussi inséré dans la variable `model`. Pour retrouver les sorties d’avant entraînement, utilisez `tuned.disable_adapter()` (voir section 6) ou redémarrez la session
- Les bibliothèques du notebook sont verrouillées aux versions vérifiées (`PINS` en section 0). Changer les versions peut empêcher son fonctionnement
