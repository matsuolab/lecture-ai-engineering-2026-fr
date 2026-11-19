"""Lecture 05 : recherche vectorielle par page."""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
)


def get_all_materials() -> str:
    """Réunir tous les documents en une chaîne avec leurs informations de cours, chapitre et page."""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"Document : {document['id']} / {document['title']}\n"
        f"Chapitre : {section['section']}\n"
        f"Page : {page.get('citation') or ('PDF p.' + str(page['page']))} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """Convertir le JSON documents → chapitres → pages en liste de pages des documents concernés."""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
                if page.get("citation"):
                    pages[-1]["citation"] = page["citation"]
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """Renvoyer la première phrase des pages directement rattachées, et le texte complet de la page demandée."""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？।॥])|(?<=[.!?؟])\s+|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("Nœud de table des matières introuvable.")


def read_page(page_id: str) -> dict:
    """Renvoyer le texte et les références d’une page des cours principaux de Lecture 01 à Lecture 03."""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("Page demandée introuvable.")


def normalized_vector(values: list[float]) -> list[float]:
    """Normaliser le vecteur pour obtenir une norme de 1."""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("L’embedding est un vecteur nul.")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Créer un embedding du texte avec Gemini. En cas de dépassement de la limite d’entrée, arrêter sans tronquer."""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"L’entrée de l’embedding dépasse la limite ou ne peut pas être mesurée : {count} tokens.")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("L’API d’embedding a tronqué le texte.")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """Ouvrir la base de recherche existante en lecture seule, puis la fermer à la sortie."""
    if not path.is_file():
        raise FileNotFoundError("Base de recherche introuvable.")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str) -> list[dict]:
    """Créer l’embedding de la question et renvoyer au plus RAG_TOP_K pages proches."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("La recherche est vide.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        columns = {column["name"] for column in db.execute("PRAGMA table_info(chunks)")}
        citation = "citation," if "citation" in columns else ""
        rows = db.execute(f"""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   {citation}
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
        return [dict(row) for row in rows]


def search_graph(query: str) -> dict:
    """Partir de la recherche vectorielle et élargir les candidats par les pages voisines et les termes communs."""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # À profondeur égale, parcourir d’abord les termes ayant le moins de connexions.
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}



def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """Fournir tous les documents en une fois et répondre sans outil de recherche."""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] Entrée : {len(prompt):,} caractères")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] Erreur API HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rechercher uniquement dans les documents de cours, sans agent")
    parser.add_argument("query", help="Sujet à rechercher")
    args = parser.parse_args()
    for i, result in enumerate(search(args.query), 1):
        print(f"\n{'=' * 60}\nRésultat de recherche {i}\n{'=' * 60}")
        print(f"Cours : {result['document_title']}")
        print(f"Chapitre : {result['section']}")
        print(f"Titre : {result['title']}")
        print(f"Page : {result.get('citation') or result['page']}")
        print(f"\n{result['content']}")
