"""Serveur MCP du glossaire et des résumés du cours 06.

    uv run python -m app.mcp_agent --list-tools
    uv run python -m app.mcp_server --http

La première commande liste les outils sans clé API. La seconde démarre un
serveur Streamable HTTP sur http://127.0.0.1:8000/mcp.

Par défaut, le serveur attend les données sur stdio. Les clients MCP comme
app.mcp_agent le lancent en sous-processus. Lancé à la main, il reste en attente.
Le même protocole donne à l’agent et aux autres clients MCP accès aux fonctions
enregistrées au cours 03.
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

# TODO(Devoir de base) : exposer aussi get_lecture_summary


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
