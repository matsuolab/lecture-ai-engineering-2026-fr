# Lecture 02 : résultats de référence obtenus par l’enseignant sur T4

Si aucun GPU n’est disponible ou si l’entraînement ne se termine pas à temps, suivez la section **4b** du notebook (`notebooks/lora_format_tuning.ipynb`) pour comparer et analyser les résultats présentés ici. Ces résultats proviennent de l’exercice original en japonais ; les résultats avec les données françaises peuvent différer.
Pour rendre le travail, réglez `executed_training_myself` sur `False` en section 7 et indiquez dans `lectures/02/answer.md` les parties exécutées vous-même.

| Fichier | Contenu |
|---|---|
| `result.json` | Configuration (`config`), versions des bibliothèques, résumés avant et après (`before` / `after`), questions ayant régressé et résultats des questions de connaissance |
| `eval_before.json` | Sorties brutes et notes des 21 questions avant entraînement |
| `eval_after.json` | Sorties brutes et notes des 21 questions après entraînement |

- Ouvrez les fichiers dans GitHub ou enregistrez-les avec « Download raw file »
- Même avec la même graine aléatoire (`seed`), l’entraînement sur GPU n’est pas parfaitement reproductible. Il est normal que les questions encore échouées diffèrent de vos résultats. Comparez les types d’échecs
