# French exercise corpus audit

## Scope and authoritative source

- `lec03-exercise.json`: all 26 canonical pages of the Japanese exercise/homework deck.
- `lec04-exercise.json`: all 23 canonical pages of the Japanese exercise/homework deck.
- Source: `../../source-documents.json`, from Japanese source commit `1ce722c2816b70ef62891a6378b2478af555e3fd`.
- Japanese uploaded decks: the top-level 26-slide `day3/第3回 演習・宿題：学習支援エージェントを作る.pptx` and the 23-slide `day4/第4回 演習・宿題：評価セットを作り、LLM に採点させる.pptx`. Exact filenames and SHA-256 hashes are recorded per page.
- No corresponding French exercise deck was supplied. All 49 pages are explicitly `new_translation_from_japanese`. There are no fabricated French file/page mappings. The supplied English exercise versions are not used as the authority.
- Terminology was checked against the existing French repository's `lectures/03/problem.md`, `lectures/04/problem.md`, `app/agent.py`, `app/tools.py`, and `data/eval/lec04_cases.jsonl` without modifying them.

## Content and intentional localization

The translation retains every substantive canonical page, including tables, commands, output examples, homework requirements, troubleshooting, and explicit image transcriptions. Repeated copyright footers are omitted on pages after the cover and recorded in provenance. Cover legal notices and copyright, logos, and the lecture 4 page 14 screenshot text are retained.

Canonical document IDs, page IDs, page numbers, section boundaries, and order remain unchanged. The one section name is translated from 全体 to `Ensemble`. Titles and prose are translated. Line wraps from slide layout are repaired; table associations are explicit.

Intentional adaptations, recorded on the affected pages:

- The two operational `git fetch` course-repository URLs point to `lecture-ai-engineering-2026-fr.git`; tag names `lec03-start` and `lec04-start` are unchanged. Research and documentation URLs are unchanged.
- Japanese lecture suffixes become `Lecture NN`, consistent with the existing French agent and its code-based check.
- The Japanese phonetic spelling example in lecture 4 page 12 becomes `Lohra`, as in the existing French evaluation dataset. Its role as a spelling variant is preserved.
- Human-readable questions, docstrings, comments, commit messages, and UI labels are translated. Executable structure, tool names, fields, flags, paths, versions, and model IDs remain intact. The source's incomplete INSTRUCTIONS/docstring excerpts are labelled as excerpts rather than represented as complete programs.
- Lecture 4 page 16 keeps the added `général ... (pass)` policy on one physical line and expands the source's abbreviated alternative into an equivalent full `général ... (fail)` line. This preserves the meaning while making copied policies compatible with the existing French `--model test` detector, whose regular expression does not span newlines.
- Existing reviewed French terminology is reused where equivalent: Bases, Mise en œuvre, Approfondissement; Ancrage, Périmètre, Indices, Clarté, Mention de séance. No old English deck was used to overwrite current Japanese content.

## Verification

`python build_exercises.py` regenerates both corpora and both per-page provenance files, and writes `exercise-validation.json`.

Passed checks:

- Exactly 26 + 23 pages, matching the source ID/page order and schema.
- All 49 pages have content and provenance; no Japanese teaching text or Unicode replacement character remains in the French corpus.
- Markdown code fences are balanced.
- Every source technical token matched by the check remains on its corresponding translated page: paths, Python files, Markdown/JSON/notebook files, flags, model IDs, versions, uppercase configuration identifiers, function identifiers, and dotted technical tokens. The only text exceptions are translated `STEP` and recorded repeated copyright footers.
- Separate per-page scans of precise decimal/version values and source URLs pass, with the intentional `-fr` repository localization applied.
- Source image transcription coverage: lecture 3 page 1; lecture 4 pages 1, 14, and 23.

Manual precision review covered the LoRA rates `0.095 → 1.0`, `0 → 0.905`, `19 / 21`, 2 remaining failures, 14 training examples/4 unsupported examples; all exercise time budgets; `Discard commits`/conflict recovery warnings; single-term glossary queries; tool registration, dummy `lecture=0` tests and nonexistent-lecture handling; `DeferredToolRequests`/`output_type`/approval/message-history sequencing; both advanced homework alternatives; and rate-limit/model fallbacks.

Lecture 4 review additionally covered human annotation of 5 criteria versus LLM judgment of 4; code-only lecture-label checking; T/F/unsure and manual review; 10 cases with 4 ordinary/6 edge cases; all mock-output numerators, denominators and `coverage 90%`; missed failures versus false alerts; reason/verdict ordering; the 3–5 benchmark questions; SWE-bench Verified 500/93/3, GPQA Diamond 198/4 choices/2 other experts, and Humanity's Last Exam 2,500/2 review rounds. The French thousands separator is written `2 500`.

Independent read-only review by the Hindi-language agent also passed on all 49 pages, including full prompt/code excerpts, image text, page/provenance hashes, the destructive-sync warnings, approval sequencing, the 5-versus-4 criterion distinction, the non-superlative Clarté wording, benchmark particulars, model IDs and numbers. No material translation issue was found. Report: `../hi/independent-review-fr-exercises.md`.

The parent agent's later functional check found that the policy example on lecture 4 page 16 initially split the keyword and `(pass)` across a physical newline. This was repaired in the builder, corpus and provenance; the equivalent explicit `(fail)` policy was also supplied. `exercise-policy-validation.json` records a dependency-free AST execution of the repository's actual `_rule_based_judge` function against the real French case 05: unchanged policy → unsure, copied pass policy → pass, copied fail policy → fail. All three checks pass. The independent reviewer also rechecked the full original, pass and fail blocks against the actual no-DOTALL regexes, confirmed that only the intended rule matches, verified all 23 provenance hashes, and confirmed that reintroducing a newline fails as a negative control. The targeted recheck passed.

## Source ambiguities retained rather than silently corrected

- Lecture 4 pages 10–11 speak of 4 criteria, while pages 8 and 14 explicitly assign 5 criteria to human annotators. The four LLM criteria and the fifth code-checked criterion are preserved as the source describes them; the wording inconsistency has not been converted into a different workflow.
- Lecture 4 page 15 calls attention to the low Clarté agreement. Its illustrative table is retained exactly: Ancrage 8/9 and Clarté 9/10, with overall 8/9 and coverage 90%. The translation does **not** claim that Clarté is the lowest rate.
- Lecture 4 page 5 retains the source's `[M times out of N]` measurement placeholder and its illustrative observed tool-call values. No measurement has been invented.
- Source approximations, pedagogical example outputs, and claims about tool behavior are translated as source material, not independently re-executed or validated against live services.

## Citation and integration limits

`page` means canonical Japanese page, never a page in an existing French exercise PDF. Both provenance files explicitly mark the absent French slide mapping. Preserve that distinction in citations and any future rendered deck.

This deliverable is translated source text for later DB construction. No DB, embeddings, API calls, repository edits, installs, commits, pushes, or merges were performed. Main lecture and graph artifacts were not changed by this exercise work. Native-speaker review and retrieval evaluation remain appropriate before publishing a full French DB.
