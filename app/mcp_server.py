"""Lecture 06 : exposer le glossaire et les résumés des séances avec un serveur MCP.

Utilisation :
    uv run python -m app.agent --mcp --list-tools   # Lister les outils exposés (sans clé API)
    uv run python -m app.mcp_server --http         # Démarrer en Streamable HTTP (http://127.0.0.1:8000/mcp)

Sans argument, écouter sur stdio (entrées/sorties standard). Un client MCP (--mcp de app.agent ou
Copilot Chat) démarre normalement ce serveur comme sous-processus. Lancé à la main, il semble bloqué,
car il attend des données en entrée.

Dans Lecture 03, les fonctions de tools.py étaient enregistrées directement dans agent.py. Avec un serveur MCP,
les mêmes fonctions deviennent accessibles de la même manière depuis d’autres clients que Pydantic AI,
comme Copilot Chat.
"""

import argparse

from mcp.server.mcpserver import MCPServer

from app import tools

# Nom et description affichés aux clients (distincts de la clé "glossary" dans la configuration)
server = MCPServer(
    "aie2026-glossary",
    instructions="Fournir le glossaire et les résumés des séances d’AI Engineering Pilot Course (AIE2026).",
)

# Exposer les mêmes fonctions que dans Lecture 03 comme outils MCP. Docstrings et annotations de types forment les descriptions
server.tool()(tools.search_glossary)

# TODO(Lecture 06 exercice) : exposer aussi tools.get_lecture_summary (même syntaxe que la ligne ci-dessus)
# Si vous avez créé make_quiz dans Lecture 03, vous pouvez aussi l’exposer


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP du glossaire")
    parser.add_argument("--http", action="store_true", help="Démarrer en Streamable HTTP (stdio par défaut)")
    args = parser.parse_args()
    if args.http:
        print("Démarrage du serveur MCP sur http://127.0.0.1:8000/mcp (Ctrl+C pour arrêter)")
        server.run(transport="streamable-http")
    else:
        # Avec stdio, la sortie standard transporte le protocole : ne pas utiliser print
        server.run()


if __name__ == "__main__":
    main()
