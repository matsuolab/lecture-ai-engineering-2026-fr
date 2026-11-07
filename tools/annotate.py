"""Lecture 04 : interface d’annotation du jeu d’évaluation (Streamlit).

Utilisation :
    uv run --with streamlit==1.66.1 streamlit run tools/annotate.py

`uv run --with` ajoute temporairement Streamlit à l’environnement du cours, sans modifier pyproject.toml.

- Annoter : afficher les cas de data/eval/lec04_cases.jsonl un par un et enregistrer les cinq verdicts
  et la case « J’hésite » dans lectures/04/labels.jsonl
- Comparer : mesurer l’accord avec les annotations de l’enseignant (lectures/04/reference/labels_instructor.jsonl)
- Créer des cas (devoir : mise en œuvre) : écrire des questions et comportements attendus dans data/eval/my_cases.jsonl.
  Faire générer les réponses par votre agent avec `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl`
"""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import tools  # noqa: E402
from app.judge import ALL_CRITERIA, check_lecture_mark, load_labels, read_jsonl, write_jsonl  # noqa: E402

DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
INSTRUCTOR_LABELS = ROOT / "lectures" / "04" / "reference" / "labels_instructor.jsonl"
MY_CASES = ROOT / "data" / "eval" / "my_cases.jsonl"

CRITERION_HELP = {
    "grounding": "Les informations du glossaire ne contredisent pas les entrées ; les informations absentes sont signalées sans affirmation non étayée",
    "scope": "La réponse reste dans l’aide à l’apprentissage du cours et refuse les questions hors sujet ou les demandes d’ignorer les instructions",
    "hint": "La réponse donne des pistes sans fournir la solution du devoir (les questions sans rapport avec un devoir réussissent)",
    "clarity": "La réponse est directe, concise et lisible",
    "lecture_mark": "La dernière ligne contient « Lecture NN » (à comparer ensuite à la vérification par code)",
}

st.set_page_config(page_title="Lecture 04 : annotation", layout="wide")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def glossary_entries(ids: list[str]) -> list[dict]:
    entries = {e["id"]: e for e in tools.load_glossary()}
    return [entries[i] for i in ids if i in entries]


# ---------------------------------------------------------------- Annoter
def page_label(cases_path: Path, labels_path: Path) -> None:
    cases = read_jsonl(cases_path)
    if not cases:
        st.error(f"Aucun cas d’évaluation dans {rel(cases_path)}")
        return
    labels = load_labels(labels_path) if labels_path.exists() else {}

    if "index" not in st.session_state:
        done = [i for i, c in enumerate(cases) if c["id"] in labels]
        st.session_state.index = min(len(done), len(cases) - 1) if done else 0

    i = st.session_state.index
    case = cases[i]
    st.progress((len(labels)) / len(cases), text=f"Enregistrés : {len(labels)} / {len(cases)} | Affichage : #{case['id']} (cas {i + 1})")

    nav1, nav2, nav3 = st.columns([1, 1, 6])
    if nav1.button("← Précédent", disabled=i == 0):
        st.session_state.index = i - 1
        st.rerun()
    if nav2.button("Suivant →", disabled=i >= len(cases) - 1):
        st.session_state.index = i + 1
        st.rerun()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"#{case['id']} — {case.get('category', '')}")
        st.markdown("**Question**")
        st.info(case["question"])
        st.markdown("**Réponse**")
        st.markdown(case["answer"] or "(Aucune réponse pour le moment. Générez-la avec `app.judge --generate`)")
        st.markdown("**Références**")
        ref = case.get("reference", {})
        entries = glossary_entries(ref.get("glossary", []))
        if entries:
            for e in entries:
                st.markdown(f"- **{e['term']}** (Lecture {e['lecture']}): {e['definition']}")
        else:
            st.markdown("- (Aucune entrée du glossaire ne correspond à cette question)")
        st.markdown(f"**Comportement attendu** : {ref.get('expected', '(non précisé)')}")

    with right:
        st.subheader("Verdicts")
        st.caption("Jugez d’après les références et la grille, plutôt que vos connaissances. En cas de doute, cochez « J’hésite » et continuez")
        current = labels.get(case["id"], {})
        with st.form(key=f"form-{case['id']}"):
            choice = {}
            for key, name in ALL_CRITERIA:
                default = 0 if current.get(key, "pass") == "pass" else 1
                choice[key] = st.radio(
                    f"{name}", ["Réussite (T)", "Échec (F)"], index=default, horizontal=True,
                    help=CRITERION_HELP[key], key=f"{case['id']}-{key}",
                )
            unsure = st.checkbox("J’hésite (la grille seule ne permet pas de trancher)", value=bool(current.get("unsure_flag", False)))
            note = st.text_input("Note (facultative)", value=current.get("note", ""))
            submitted = st.form_submit_button("Enregistrer et continuer", type="primary")
        if submitted:
            labels[case["id"]] = {
                "id": case["id"],
                **{key: ("pass" if choice[key].startswith("Réussite") else "fail") for key, _ in ALL_CRITERIA},
                "unsure_flag": unsure,
                "note": note,
            }
            write_jsonl(labels_path, [labels[c["id"]] for c in cases if c["id"] in labels])
            if i < len(cases) - 1:
                st.session_state.index = i + 1
            st.rerun()

    if len(labels) >= len(cases):
        st.success(f"Les {len(cases)} cas sont enregistrés → {rel(labels_path)}. Faites-les évaluer par un LLM avec `uv run python -m app.judge`")
        st.dataframe(
            [{"id": c["id"], **{name: labels[c["id"]][key] for key, name in ALL_CRITERIA},
              "J’hésite": labels[c["id"]].get("unsure_flag", False)} for c in cases if c["id"] in labels],
            hide_index=True, use_container_width=True,
        )


# ---------------------------------------------------------------- Comparer
def page_compare(cases_path: Path, labels_path: Path) -> None:
    if not labels_path.exists():
        st.warning("Enregistrez d’abord vos annotations dans « Annoter »")
        return
    if not INSTRUCTOR_LABELS.exists():
        st.warning(f"Annotations de l’enseignant introuvables : {rel(INSTRUCTOR_LABELS)}")
        return
    cases = read_jsonl(cases_path)
    mine, ref = load_labels(labels_path), load_labels(INSTRUCTOR_LABELS)
    ids = [c["id"] for c in cases if c["id"] in mine and c["id"] in ref]
    st.subheader("Accord entre vos annotations et celles de l’enseignant")
    st.caption("Les annotations de l’enseignant ne sont pas nécessairement les bonnes réponses ; elles montrent que les humains peuvent aussi être en désaccord")
    cols = st.columns(len(ALL_CRITERIA))
    for col, (key, name) in zip(cols, ALL_CRITERIA):
        agree = sum(1 for cid in ids if mine[cid].get(key) == ref[cid].get(key))
        col.metric(name, f"{agree}/{len(ids)}")
    code_agree = sum(1 for cid in ids if mine[cid].get("lecture_mark") == check_lecture_mark(next(c for c in cases if c["id"] == cid)["answer"]))
    st.caption(f"Mention de séance : vos verdicts et le code concordent sur {code_agree}/{len(ids)} cas")
    rows = []
    for cid in ids:
        for key, name in ALL_CRITERIA:
            if mine[cid].get(key) != ref[cid].get(key):
                rows.append({"id": cid, "Critère": name, "Vous": mine[cid].get(key), "Enseignant": ref[cid].get(key),
                             "Vous avez hésité": mine[cid].get("unsure_flag", False), "Note de l’enseignant": ref[cid].get("note", "")})
    st.markdown(f"**Points en désaccord : {len(rows)}**")
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Créer des cas (devoir : mise en œuvre)
def page_author(cases_path: Path) -> None:
    st.subheader("Créer votre jeu d’évaluation (devoir : mise en œuvre)")
    st.caption("Écrivez une question et le comportement attendu. Faites générer la réponse par votre agent avec `uv run python -m app.judge --generate --cases "
               f"{rel(cases_path)}`. Incluez des cas ordinaires et des entrées susceptibles de provoquer des échecs (cas limites)")
    existing = read_jsonl(cases_path) if cases_path.exists() else []
    glossary = tools.load_glossary()
    options = {f"{e['term']} (Lecture {e['lecture']})": e["id"] for e in glossary}
    with st.form("author"):
        question = st.text_area("Question", height=80)
        category = st.text_input("Catégorie (cas ordinaire, terme absent du glossaire, hors du cours, etc.)")
        expected = st.text_area("Comportement attendu (une ou deux phrases)", height=80)
        picked = st.multiselect("Entrées du glossaire à utiliser comme références", list(options))
        submitted = st.form_submit_button("Ajouter", type="primary")
    if submitted:
        if not question.strip() or not expected.strip():
            st.error("La question et le comportement attendu sont obligatoires")
        else:
            existing.append({
                "id": f"{len(existing) + 1:02d}", "category": category.strip(),
                "question": question.strip(), "answer": "",
                "reference": {"glossary": [options[p] for p in picked], "expected": expected.strip()},
            })
            write_jsonl(cases_path, existing)
            st.success(f"Ajout effectué ({len(existing)} cas) → {rel(cases_path)}")
    if existing:
        st.dataframe([{"id": c["id"], "Catégorie": c.get("category", ""), "Question": c["question"],
                       "Réponse présente": bool(c.get("answer"))} for c in existing], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Navigation entre les écrans
def main() -> None:
    st.markdown("## Lecture 04 : annoter le jeu d’évaluation")
    with st.sidebar:
        mode = st.radio("Écran", ["Annoter", "Comparer (avec l’enseignant)", "Créer des cas (devoir : mise en œuvre)"])
        st.divider()
        cases_path = Path(st.text_input("Jeu d’évaluation", value=rel(DEFAULT_CASES)))
        labels_path = Path(st.text_input("Destination des annotations", value=rel(DEFAULT_LABELS)))
        my_cases_path = Path(st.text_input("Destination des nouveaux cas", value=rel(MY_CASES)))
    cases_path = cases_path if cases_path.is_absolute() else ROOT / cases_path
    labels_path = labels_path if labels_path.is_absolute() else ROOT / labels_path
    my_cases_path = my_cases_path if my_cases_path.is_absolute() else ROOT / my_cases_path

    if mode.startswith("Annoter"):
        page_label(cases_path, labels_path)
    elif mode.startswith("Comparer"):
        page_compare(cases_path, labels_path)
    else:
        page_author(my_cases_path)


main()
