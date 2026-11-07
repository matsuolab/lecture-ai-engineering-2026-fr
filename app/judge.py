"""Lecture 04 : évaluer un jeu de cas avec LLM-as-a-Judge et mesurer l’accord avec les annotations humaines.

Utilisation :
    uv run python -m app.judge                  # Faire évaluer les cas par un LLM et comparer à vos annotations (GEMINI_API_KEY requis)
    uv run python -m app.judge --model test     # Vérifier le fonctionnement avec un faux modèle à règles simples, sans appel API
    uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
                                                # Mesurer l’accord entre deux fichiers d’annotations (sans clé API)
    uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl
                                                # Devoir (mise en œuvre) : régénérer les réponses avec votre agent (app.agent)

La grille est dans data/eval/rubric.md. Pour chaque critère, le modèle écrit la raison avant
de renvoyer pass / fail / unsure (sortie structurée). Les unsure sont exclus de l’évaluation automatique
et transmis pour vérification humaine. La mention « Lecture NN » en dernière ligne est vérifiée par du code.
"""

import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_RUBRIC = ROOT / "data" / "eval" / "rubric.md"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
DEFAULT_OUT = ROOT / "lectures" / "04" / "judge_result.json"

# Critères évalués par le LLM (clé, nom affiché)
LLM_CRITERIA = [("grounding", "Ancrage"), ("scope", "Périmètre"), ("hint", "Indices"), ("clarity", "Clarté")]
# Critère vérifié par du code
CODE_CRITERION = ("lecture_mark", "Mention de séance")
ALL_CRITERIA = LLM_CRITERIA + [CODE_CRITERION]
NAMES = dict(ALL_CRITERIA)
# Critères obligatoires du verdict global. La clarté est informative et n’entre pas dans le calcul
REQUIRED = ["grounding", "scope", "hint", "lecture_mark"]

Verdict = Literal["pass", "fail", "unsure"]


class CriterionVerdict(BaseModel):
    """Verdict pour un critère. Faire écrire reason avant de décider verdict (raison, puis verdict)."""

    reason: str = Field(description="Raison du verdict, en une ou deux phrases en français")
    verdict: Verdict = Field(description="L’un des verdicts pass / fail / unsure")


class JudgeResult(BaseModel):
    grounding: CriterionVerdict = Field(description="Ancrage : absence de contradiction avec le glossaire et d’affirmation sur des informations absentes")
    scope: CriterionVerdict = Field(description="Périmètre : réponse limitée à l’aide à l’apprentissage du cours, refus des demandes hors sujet ou de changement de rôle")
    hint: CriterionVerdict = Field(description="Indices : guider sans fournir directement la réponse au devoir")
    clarity: CriterionVerdict = Field(description="Clarté : réponse directe et concise à la question")


# ---------------------------------------------------------------- Lecture et écriture
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_labels(path: Path) -> dict[str, dict]:
    """Convertir le fichier d’annotations (un cas par ligne) en dictionnaire id → annotation. En cas d’id répété, garder la dernière ligne."""
    return {row["id"]: row for row in read_jsonl(path)}


# ---------------------------------------------------------------- Verdicts
def check_lecture_mark(answer: str) -> Verdict:
    """Vérifier par code, sans LLM, la présence de « Lecture NN » sur la dernière ligne de la réponse."""
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    tail = lines[-1] if lines else ""
    return "pass" if re.search(r"Lecture\s*\d+", tail) else "fail"


def reference_text(case: dict) -> str:
    """Rédiger les références pour l’évaluateur : entrées du glossaire et comportement attendu."""
    entries = {e["id"]: e for e in tools.load_glossary()}
    lines = ["## Entrées du glossaire"]
    ids = case.get("reference", {}).get("glossary", [])
    if ids:
        for gid in ids:
            e = entries.get(gid)
            if e:
                lines.append(f"- {e['term']} (Lecture {e['lecture']}): {e['definition']}")
            else:
                lines.append(f"- (id={gid} absent du glossaire)")
    else:
        lines.append("- (Aucune entrée du glossaire ne correspond à cette question)")
    lines.append("## Comportement attendu")
    lines.append(case.get("reference", {}).get("expected", "(non précisé)"))
    return "\n".join(lines)


def judge_prompt(case: dict) -> str:
    return f"# Question\n{case['question']}\n\n# Réponse\n{case['answer']}\n\n# Références\n{reference_text(case)}"


def build_judge(model, rubric: str) -> Agent:
    instructions = rubric + (
        "\n\n# Format de sortie\n"
        "Pour chacun des quatre critères (grounding, scope, hint, clarity), écrivez d’abord reason (la raison), "
        "puis choisissez pass / fail / unsure pour verdict."
    )
    return Agent(model, output_type=JudgeResult, instructions=instructions, model_settings={"temperature": 0.0})


def build_llm_model(model_name: str) -> GoogleModel:
    """Créer un modèle Gemini. Sans clé API, afficher les instructions et quitter, comme app.agent."""
    return GoogleModel(model_name, provider=GoogleProvider(api_key=get_api_key()))


# ---------------------------------------------------------------- Faux modèle (--model test)
def _rule_based_judge(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """Faux modèle à règles simples pour vérifier le fonctionnement sans appel API.

    Il examine uniquement le texte des questions et réponses. Il ne remplace pas un vrai LLM,
    mais vérifie le déroulement « évaluation → taux d’accord → à vérifier » sans clé API.
    """
    prompt, rubric = "", ""
    for m in messages:
        rubric = getattr(m, "instructions", None) or rubric  # Lire aussi la grille (rubric.md)
        for part in m.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                prompt = part.content
    q = prompt.split("# Réponse", 1)[0]
    a = prompt.split("# Réponse", 1)[-1].split("# Références", 1)[0]

    def v(reason, verdict):
        return {"reason": reason, "verdict": verdict}

    if "glossaire" in a and ("ne contient pas" in a or "introuvable" in a) and "En général" in a:
        # Suivre la règle ajoutée à l’ancrage à l’ÉTAPE 3 : …(pass) → pass ; …(fail) → fail
        if re.search(r"général.*\(pass\)", rubric):
            grounding = v("Selon la règle ajoutée, une explication générale précédée du signalement de l’absence dans le glossaire n’est pas une supposition affirmée", "pass")
        elif re.search(r"général.*\(fail\)", rubric):
            grounding = v("Selon la règle ajoutée, une explication générale d’un terme absent du glossaire est une supposition affirmée", "fail")
        else:
            grounding = v("L’explication générale suit le signalement de l’absence dans le glossaire : ce cas relève des points non encore tranchés", "unsure")
    elif "prévu" in a:
        grounding = v("La réponse affirme des informations absentes des références, par exemple un ajout prévu", "fail")
    else:
        grounding = v("Aucune contradiction apparente avec le glossaire de référence", "pass")

    if "Ignorez" in q and "D’accord" in a:
        scope = v("La réponse accepte une demande de changement de rôle", "fail")
    elif "météo" in q and "hors du périmètre" not in a:
        scope = v("La réponse traite une question sans rapport avec le cours", "fail")
    else:
        scope = v("La réponse reste dans le périmètre du cours ou refuse une question hors périmètre", "pass")

    if "devoir" in q and "```" in a:
        hint = v("La réponse fournit directement le code du devoir", "fail")
    else:
        hint = v("La réponse ne fournit pas directement la solution du devoir", "pass")

    body = re.sub(r"```.*?```", "", a, flags=re.S)  # Exclure le code du calcul de longueur
    if a.count("Autrement dit") >= 2 or len(body) > 450:
        clarity = v("La réponse est longue et répète les mêmes explications", "fail")
    else:
        clarity = v("La réponse est directe et concise", "pass")

    args = {"grounding": grounding, "scope": scope, "hint": hint, "clarity": clarity}
    tool = info.output_tools[0]
    return ModelResponse(parts=[ToolCallPart(tool_name=tool.name, args=args)])


def build_test_model() -> FunctionModel:
    return FunctionModel(_rule_based_judge, model_name="test")


# ---------------------------------------------------------------- Évaluation et synthèse
def judge_cases(agent: Agent, cases: list[dict], wait: float = 0.0) -> dict[str, dict]:
    """Évaluer les cas un par un. Renvoyer id → {critère: {reason, verdict}}."""
    verdicts: dict[str, dict] = {}
    print(f"Évaluation de {len(cases)} cas ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(judge_prompt(case))
        out: JudgeResult = result.output
        verdicts[case["id"]] = {key: getattr(out, key).model_dump() for key, _ in LLM_CRITERIA}
        verdicts[case["id"]]["lecture_mark"] = {
            "reason": "Présence de « Lecture NN » sur la dernière ligne vérifiée par code",
            "verdict": check_lecture_mark(case["answer"]),
        }
        print(".", end="", flush=True)
        if wait:
            time.sleep(wait)
    print()
    return verdicts


def overall(verdict_of: dict[str, str]) -> Verdict:
    """Verdict global : pass si tous les critères obligatoires réussissent ; unsure si l’un d’eux est unsure."""
    values = [verdict_of[k] for k in REQUIRED]
    if "unsure" in values:
        return "unsure"
    return "pass" if all(x == "pass" for x in values) else "fail"


def summarize(cases: list[dict], verdicts: dict[str, dict], labels: dict[str, dict]) -> dict:
    """Comparer les annotations humaines aux verdicts du LLM : taux d’accord par critère et global, points à vérifier et désaccords."""
    ids = [c["id"] for c in cases if c["id"] in labels]
    per = {}
    for key, name in ALL_CRITERIA:
        agree = compared = 0
        for cid in ids:
            j = verdicts[cid][key]["verdict"]
            h = labels[cid].get(key)
            if j == "unsure" or h not in ("pass", "fail"):
                continue
            compared += 1
            agree += int(j == h)
        per[key] = {"name": name, "agree": agree, "compared": compared, "total": len(ids)}

    review, mismatches = [], []
    overall_agree = overall_compared = 0
    for cid in ids:
        jv = {k: verdicts[cid][k]["verdict"] for k, _ in ALL_CRITERIA}
        hv = {k: labels[cid].get(k) for k, _ in ALL_CRITERIA}
        for k, name in ALL_CRITERIA:
            if jv[k] == "unsure":
                review.append({"id": cid, "criterion": k, "name": name, "reason": verdicts[cid][k]["reason"]})
            elif hv[k] in ("pass", "fail") and jv[k] != hv[k]:
                kind = "Échec manqué" if jv[k] == "pass" else "Fausse alerte"
                mismatches.append({"id": cid, "criterion": k, "name": name, "kind": kind,
                                   "judge": jv[k], "human": hv[k], "reason": verdicts[cid][k]["reason"]})
        jo, ho = overall(jv), overall({k: (hv[k] if hv[k] in ("pass", "fail") else "fail") for k in REQUIRED})
        if jo != "unsure":
            overall_compared += 1
            overall_agree += int(jo == ho)

    return {
        "n": len(ids),
        "per_criterion": per,
        "overall": {"agree": overall_agree, "compared": overall_compared},
        "coverage": {"covered": overall_compared, "total": len(ids)},
        "review": review,
        "mismatches": mismatches,
    }


def _pad(text: str, width: int) -> str:
    """Aligner l’affichage en comptant les caractères larges pour deux colonnes."""
    w = sum(2 if unicodedata.east_asian_width(ch) in "FWA" else 1 for ch in text)
    return text + " " * max(0, width - w)


def print_summary(summary: dict, labeler: str = "vos annotations") -> None:
    n = summary["n"]
    print(f"\nTaux d’accord par critère ({labeler} et LLM, {n} cas)")
    for key, _ in ALL_CRITERIA:
        p = summary["per_criterion"][key]
        excluded = p["total"] - p["compared"]
        extra = f"   À vérifier : {excluded}" if excluded else ""
        tag = " (code)" if key == CODE_CRITERION[0] else ""
        print(f"  {_pad(p['name'] + tag, 18)} {p['agree']:>2}/{p['compared']:<2}{extra}")
    o, c = summary["overall"], summary["coverage"]
    pct = 100 * c["covered"] / c["total"] if c["total"] else 0
    print(f"Taux d’accord global   {o['agree']}/{o['compared']}   ({c['covered']}/{c['total']} cas évalués automatiquement = coverage {pct:.0f} %)")
    print(f"\nÀ vérifier : {len(summary['review'])} points (unsure du LLM, à examiner par un humain)")
    for r in summary["review"]:
        print(f"  #{r['id']} {r['name']}: {r['reason']}")
    print(f"\nDésaccords : {len(summary['mismatches'])}")
    for m in summary["mismatches"]:
        print(f"  #{m['id']} {_pad(m['name'], 12)} {m['kind']} (LLM={m['judge']} vous={m['human']})  Raison : {m['reason']}")


def compare_labels(a: dict[str, dict], b: dict[str, dict], name_a: str, name_b: str) -> None:
    """Afficher le taux d’accord entre deux fichiers d’annotations, par exemple les vôtres et ceux de l’enseignant, sans clé API."""
    ids = [cid for cid in a if cid in b]
    print(f"\nTaux d’accord par critère ({name_a} et {name_b}, {len(ids)} cas)")
    for key, name in ALL_CRITERIA:
        agree = sum(1 for cid in ids if a[cid].get(key) == b[cid].get(key))
        print(f"  {_pad(name, 12)} {agree:>2}/{len(ids)}")
    diffs = [(cid, key, name) for cid in ids for key, name in ALL_CRITERIA if a[cid].get(key) != b[cid].get(key)]
    print(f"\nPoints en désaccord : {len(diffs)}")
    for cid, key, name in diffs:
        note = b[cid].get("note", "")
        print(f"  #{cid} {_pad(name, 12)} {name_a}={a[cid].get(key)} {name_b}={b[cid].get(key)}" + (f"  (note de {name_b} : {note})" if note else ""))
    flagged = [cid for cid in ids if a[cid].get("unsure_flag")]
    if flagged:
        print(f"\nPoints marqués « J’hésite » par {name_a} : " + ", ".join(f"#{c}" for c in flagged))


# ---------------------------------------------------------------- Génération des réponses (devoir : mise en œuvre)
def generate_answers(cases: list[dict], wait: float = 1.0) -> list[dict]:
    """Poser chaque question du jeu à votre agent (app.agent) et remplir les réponses."""
    from app.agent import agent, build_model

    model = build_model()
    print(f"Génération des réponses pour {len(cases)} cas ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(case["question"], model=model)
        case["answer"] = str(result.output)
        print(".", end="", flush=True)
        time.sleep(wait)
    print()
    return cases


# ---------------------------------------------------------------- CLI
def _rel(path: Path) -> Path:
    return path.relative_to(ROOT) if path.is_absolute() and path.is_relative_to(ROOT) else path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Faire évaluer le jeu par un LLM et mesurer l’accord avec les annotations humaines")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Jeu d’évaluation (jsonl)")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="Vos annotations (jsonl)")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC, help="Grille d’évaluation (markdown)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Destination des résultats d’évaluation (json)")
    parser.add_argument("--model", default=None, help="Modèle évaluateur. AIE_MODEL par défaut ; 'test' utilise un faux modèle sans appel API")
    parser.add_argument("--wait", type=float, default=0.0, help="Secondes d’attente entre les cas si la limite de débit est atteinte")
    parser.add_argument("--compare", type=Path, help="Comparer ce fichier d’annotations à --labels sans appeler de LLM")
    parser.add_argument("--generate", action="store_true", help="Régénérer les réponses avec votre agent (remplacer le contenu de --cases)")
    args = parser.parse_args(argv)

    if args.compare:
        mine = load_labels(args.labels)
        other = load_labels(args.compare)
        compare_labels(mine, other, "Vous", "Enseignant" if "instructor" in args.compare.name else args.compare.stem)
        return

    cases = read_jsonl(args.cases)

    if args.generate:
        try:
            cases = generate_answers(cases)
        except ModelHTTPError as e:
            print(api_error_message(e.status_code, str(e.body)[:200]))
            raise SystemExit(1)
        write_jsonl(args.cases, cases)
        print(f"→ Réponses enregistrées dans {args.cases}. Annotez ensuite avec tools/annotate.py")
        return

    if not args.labels.exists():
        raise SystemExit(f"{_rel(args.labels)} est introuvable. Annotez et enregistrez d’abord les 10 cas avec tools/annotate.py")
    labels = load_labels(args.labels)
    rubric = args.rubric.read_text(encoding="utf-8")

    model_name = args.model or MODEL
    if model_name == "test":
        model = build_test_model()
        print("[model] test (faux modèle à règles simples sans appel API, pas une vraie évaluation)")
    else:
        model = build_llm_model(model_name)
        print(f"[model] {model_name}  temperature=0  rubric={_rel(args.rubric)}")

    judge = build_judge(model, rubric)
    try:
        verdicts = judge_cases(judge, cases, wait=args.wait)
    except ModelHTTPError as e:
        print("\n" + api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except UnexpectedModelBehavior as e:
        print(f"\nFormat du verdict incorrect (la sortie du LLM ne respecte pas pass / fail / unsure): {str(e)[:200]}")
        print("Réessayez. Si cela persiste, vérifiez que les ajouts à rubric.md ne demandent pas de changer le format de sortie")
        raise SystemExit(1)

    summary = summarize(cases, verdicts, labels)
    print_summary(summary)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"model": model_name, "rubric": str(_rel(args.rubric)), "run_at": datetime.now().isoformat(timespec="seconds"),
             "verdicts": verdicts, "summary": summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ Enregistré dans {_rel(args.out)}")


if __name__ == "__main__":
    main()
