"""Configuration commune à tout le cours.

Lire la clé API et le nom du modèle dans les variables d’environnement, sans les inscrire dans le code.
"""

import os
from pathlib import Path

# Modèle par défaut. Définir AIE_MODEL pour en choisir un autre.
#   Exemple : export AIE_MODEL=gemini-3.5-flash
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MODEL = os.getenv("AIE_MODEL", DEFAULT_MODEL)


# Lecture 05 : une page par fragment de recherche. Créer l’index avec scripts/build_rag_index.py.
ROOT = Path(__file__).resolve().parent.parent
RAG_SOURCE = ROOT / "data/rag_data/lectures.json"
RAG_TREE = ROOT / "data/rag_data/tree.json"
RAG_GRAPH = ROOT / "data/rag_data/graph.json"
RAG_DB = Path(os.getenv("AIE_RAG_DB", str(ROOT / "data/rag_data/index.sqlite3")))
RAG_DOCUMENT_IDS = ("lec01-main", "lec02-main", "lec03-main")
RAG_TOP_K = 5
GRAPH_START_K = 3
GRAPH_HOPS = 2
GRAPH_MAX_RESULTS = 10
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
# Réserver une marge sous la limite de 2 048 tokens pour la tâche et autres éléments. En cas de dépassement, arrêter sans tronquer.
EMBEDDING_MAX_TOKENS = 2000


def api_error_message(status: int, detail: str = "") -> str:
    """Convertir un code HTTP en explication en français pour les apprenants (partagé par ask.py et agent.py)."""
    if status == 429:
        return "Limite de débit atteinte. Attendez environ une minute, puis réessayez."
    if status == 503:
        return "Le modèle est saturé (503). Attendez un peu, puis réessayez."
    if status in (400, 401, 403, 404):
        return f"Problème de clé API ou de nom de modèle ({status}) : {detail}"
    return f"Erreur API ({status}) : {detail}"


def get_api_key() -> str:
    """Renvoyer GEMINI_API_KEY. Si elle manque, afficher les instructions et quitter."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "La variable d’environnement GEMINI_API_KEY est introuvable.\n"
            "1. Dans GitHub, ajoutez GEMINI_API_KEY sous Settings → Codespaces → Secrets,\n"
            "   puis sélectionnez votre fork parmi les dépôts autorisés.\n"
            "2. Si vous l’avez ajoutée après le démarrage de Codespaces, redémarrez Codespaces.\n"
            "   (En bas à gauche : « Codespaces » → « Stop Current Codespace » → rouvrir)"
        )
    return key
