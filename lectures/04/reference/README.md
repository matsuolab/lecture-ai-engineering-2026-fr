# Lecture 04 : références

- `labels_instructor.jsonl` contient les annotations de l’enseignant. Le champ `note` explique le verdict et les échecs introduits volontairement.
  Ces annotations ne constituent pas nécessairement les bonnes réponses : elles servent à montrer que les humains peuvent aussi être en désaccord.

Pour les comparer à vos annotations (`lectures/04/labels.jsonl`), utilisez l’écran « Comparer » de `tools/annotate.py` ou la commande suivante :

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

## Observations avec le vrai évaluateur (gemini-3.5-flash-lite)

Voici les résultats obtenus en exécutant `app.judge` avec les annotations de l’enseignant comme annotations personnelles, puis les modifications apportées à `rubric.md` et au jeu d’évaluation. Ces observations proviennent de l’exécution originale en japonais ; l’évaluation par LLM n’a pas été mesurée en français dans cette mise à jour.

| Observation | Modification |
|---|---|
| #02, ancrage : fail à cause de « mentionner Lecture 03 en dernière ligne » dans le comportement attendu, alors que la mention de séance est vérifiée par du code | Retrait de « mentionner Lecture NN en dernière ligne » du comportement attendu ; ajout dans rubric.md de « ne pas inclure ici la mention de séance » |
| #06 et #08, clarté : fail pour les mêmes raisons que celles déjà retenues pour les indices ou le périmètre | Précision dans la clarté : « examiner uniquement la lisibilité ; les autres critères évaluent le contenu et le rôle » ; ajout de « examiner les critères indépendamment » à la méthode |
| #04, clarté : pass malgré une réponse longue qui répète la même explication | Précision : « les reformulations ou répétitions du même contenu, par exemple après “Autrement dit”, reçoivent fail » |
| #05, ancrage : pass au lieu de unsure, le juge décidant lui-même d’un point non défini dans la grille | Ajout de la section « Points non encore tranchés », avec la consigne de répondre unsure dans ces cas. À l’ÉTAPE 3, une règle est décidée pour ce point et ajoutée à la grille |

Le modèle évaluateur tend à choisir pass ou fail même pour les points non définis. Avant le cours, réexécutez l’évaluation avec la grille modifiée et vérifiez si #05 reçoit unsure.
