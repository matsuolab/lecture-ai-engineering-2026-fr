# French Lecture 03 corpus audit

Prepared 71 canonical page records for `lec03-main`, using the uploaded French slides and the current Japanese source at `1ce722c2816b70ef62891a6378b2478af555e3fd`.

## Deliverables

- `lec03-main.json`: the same document/section/page schema and stable IDs as the Japanese corpus, with French titles and full teaching content.
- `provenance.json`: every canonical page's actual French slide number and uploaded filename, source revision, file/content hashes, and individual corrections. New translations are explicitly identified.
- `graph-terms.json`: 72 translated term nodes, retaining every original node ID, kind, and technical English alias.
- `build_corpus.py` and `build_graph_terms.py`: reproducible assembly and validation, with literal correction assertions.
- `validation.json`: page and correction counts; no DB/API execution is claimed.

## Version and page correspondence

The French `Cours 3 - Agents d_IA_fr.pptx` has 69 slides. The Japanese final `AIE2026_第3回_AIエージェント_1102.pptx` and current corpus have 71 pages. The 69 French slides correspond to the Japanese `draft-1031b` deck, not directly to the final PDF page numbers.

- French slides 3 and 4 correspond to final Japanese pages 4 and 3, respectively.
- Final Japanese page 32 (tool search) has no French slide. It was translated from the canonical source.
- Final Japanese page 58 (self-improvement of the harness) has no French slide. It was translated from the canonical source.
- Subsequent pages shift by one or two positions. The complete mapping is stored per page in `provenance.json`.

`page` in this corpus is the canonical Japanese page number, required to retain source IDs and section alignment. **It must not be presented as the page number of the supplied French PDF.** Consumers must use the separate actual slide number or explicitly label citations as the Japanese final source page. The two new translations have no page in the supplied French PDF.

## Fidelity review and repairs

Compared all 71 canonical source pages with the corresponding French slide text. Reused existing French wording where it preserved the meaning. The corpus contains full page text, not summaries.

The final source changes were translated on pages 3, 24, 26, 28, 29, 31, 34, 36, 50, 53, and 59; pages 32 and 58 were newly translated. Per-page provenance lists the exact changes.

Additional inherited omissions or inaccuracies were repaired:

- Page 19: restored both chart axes, the 99% and 95% curve labels, METR graph labels, and displayed model names from the explicit canonical transcription. Rendered and inspected Japanese PDF page 19 to verify left/right chart association. No curve-point values were invented.
- Pages 4 and 59: restored omitted tool-calling and harness parts of headings.
- Page 29: corrected the inherited resident-agent cross-reference from Part 3 to source Part 2.
- Page 39: restored the **first** 200 lines / 25 KB limit and fixed a joined word.
- Page 44: restored that an unmet goal's reason is sent back before continuing.
- Pages 61–70: repaired abbreviated qualifications, attribution, and omissions. These include checking permissions in the harness, treating an 8% cost increase as one evaluation result, retaining the 95%-per-step assumption, distinguishing a page addendum's date from the date of a numeric finding, and specifying which disclosure omitted a model's identity.
- Page 70: restored the source's “one hundredth or less” inequality; the existing French wording incorrectly made it strictly less than one hundredth.

Repeated copyright footers were removed from retrieval text to reduce boilerplate; original text remains in extraction artifacts, and removed lines are logged in provenance. The title slide's restriction notice and explicitly transcribed logo remain. Technical commands, source URLs, model identifiers, examples, and caveats remain teaching data; no embedded instruction was executed.

## Validation completed

An independent source-fidelity review by the Hindi language agent identified five additional precision issues, now corrected in the reproducible builder and per-page provenance: graduate-school affiliation (page 2), new **type** of operation (25), avoiding an all-tools claim (66), **at least** 90% (69), and detection **within** 15 minutes (70).

- 71 pages; every source document/section/page ID and page ordering preserved.
- 69 unique uploaded-slide correspondences plus 2 explicitly labeled new source translations.
- All French content and metadata parse as UTF-8 JSON; no Japanese prose or replacement-character corruption remains in translated text.
- Source technical model/version/arXiv/identifier tokens checked against the resulting corpus; no missing tokens found.
- The source URL on page 28 is retained exactly, with only surrounding French punctuation differing.
- Graph term count and IDs match the 72-node source; all technical English aliases are retained.
- Reproducible scripts use assertion-checked replacements and page/content hashes.

## Limits and integration requirements

This is a reviewed **text corpus for Lecture 03 only**, not a finished retrieval database. No embeddings, index regeneration, paid API calls, model-based retrieval evaluation, publication, or repository changes were performed.

The French deck is an older translated version. This corpus incorporates documented translations of final Japanese additions, so it is intentionally not a verbatim reproduction of the 69-slide French deck. Those additions need to remain distinguishable in citations and provenance. The corpus's canonical page numbering cannot silently replace translated PDF numbering.

The review used editable PPTX text, the authoritative Japanese transcription, and a visual check of the missing chart transcription on page 19. It did not render and independently OCR every image on every slide. No independent native-speaker sign-off is claimed. Technical claims and historical dates are preserved as source assertions rather than externally re-verified.

Parent integration still needs the other requested lecture documents, consistent citation metadata, corpus/tree/graph assembly, actual embeddings with the selected model, and multilingual retrieval/evidence checks. The graph term file contains labels and aliases only; it does not create or alter graph edges.
