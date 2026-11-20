"""Agent d’aide à l’apprentissage et client MCP du cours 06.

    uv run python -m app.mcp_agent --list-tools
    uv run python -m app.mcp_agent --trace "Qu’est-ce que LoRA ?"

Au cours 03, l’agent enregistrait directement les fonctions de tools.py. Ici,
il découvre les outils proposés par les serveurs définis dans app/mcp_servers.json.
Le principe du modèle, de la boucle et des outils reste le même.
"""

import argparse
import inspect
import json
from pathlib import Path

from fastmcp import Client
from mcp.shared.exceptions import MCPError
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app.config import MODEL, api_error_message, get_api_key

# Guider l’utilisation du glossaire et des autres serveurs configurés.
INSTRUCTIONS = """\
Vous êtes l’agent d’aide à l’apprentissage du cours d’ingénierie de l’IA (AIE2026). Répondez en français.
- Consultez le glossaire avec search_glossary avant de répondre sur des termes ou sur le cours.
- Utilisez get_lecture_summary pour les questions sur le contenu d’une séance.
- Si le glossaire ne contient pas le terme, dites-le et évitez de deviner.
- Terminez la réponse par le numéro de la séance correspondante (Lecture N).
- Donnez des pistes pour que les étudiants résolvent eux-mêmes leurs devoirs.
- Pour ce que le glossaire ne couvre pas, comme une page web ou la documentation AWS, utilisez un outil adapté s’il est disponible.
"""

# Configuration des serveurs au format "mcpServers" de Claude Desktop et Cursor.
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


class ConfigError(Exception):
    """Erreur dans la configuration app/mcp_servers.json."""


def read_config(config_path: Path = MCP_CONFIG) -> dict:
    """Renvoie les noms et les paramètres des serveurs de l’objet mcpServers."""
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON non valide près de la ligne {e.lineno} ({e.msg})") from e
    except KeyError as e:
        raise ConfigError('Clé "mcpServers" manquante') from e
    for name, spec in config.items():
        if "command" not in spec and "url" not in spec:
            raise ConfigError(f'Le serveur "{name}" doit définir "command" ou "url"')
    return config


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """Crée un ensemble d’outils MCP pour chaque serveur configuré.

    command lance un sous-processus stdio. url relie l’agent à un serveur
    déjà actif via Streamable HTTP. Le nom du serveur préfixe celui
    de l’outil pour distinguer les outils portant le même nom.

    Pydantic AI propose load_mcp_toolsets(). Fixer le mode legacy évite
    les avertissements de détection automatique avec d’anciens SDK comme fetch.
    """
    toolsets = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def describe_servers(config_path: Path = MCP_CONFIG) -> list[str]:
    """Décrit le mode de lancement ou de connexion de chaque serveur."""
    lines = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            lines.append(f"[server] {name}: connexion à l’URL ({spec['url']})")
        else:
            command = " ".join([spec["command"], *spec.get("args", [])])
            lines.append(f"[server] {name}: lancement par la commande ({command})")
    return lines


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """Construit un agent doté d’outils MCP. Le modèle est fourni à l’exécution."""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """Affiche les noms, descriptions et arguments avec un modèle de test.

    TestModel donne accès aux définitions sans appeler de LLM.
    """
    model = TestModel(call_tools=[])
    target.run_sync("Liste des outils", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"Outils visibles par le modèle : {len(tools_seen)}")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  Arguments: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """Affiche les appels d’outils, leurs arguments et leurs résultats."""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
            elif isinstance(part, RetryPromptPart) and part.tool_name:
                # Le modèle peut utiliser cette erreur pour décider de réessayer.
                print(f"[tool error]  {part.tool_name} -> {str(part.content)[:120]}")
    usage = result.usage
    print(f"[usage] entrée {usage.input_tokens:,} tokens / sortie {usage.output_tokens:,} tokens / réponses du modèle {usage.requests}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poser une question à l’agent d’aide doté d’outils MCP")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="Afficher les appels d’outils")
    parser.add_argument("--list-tools", action="store_true", help="Lister les outils visibles par le modèle, puis quitter (sans clé API)")
    args = parser.parse_args()
    if not args.list_tools and not args.question:
        parser.error("Indiquez une question")

    try:
        target = build_mcp_agent()
        print("\n".join(describe_servers()))
    except ConfigError as e:
        print(f"Impossible de lire app/mcp_servers.json: {e}")
        print("Vérifiez la virgule entre chaque serveur et l’absence de virgule après le dernier.")
        raise SystemExit(1)
    try:
        if args.list_tools:
            print_tools(target)
            return
        model = build_model()
        print(f"[model] {MODEL}")
        print(f"[tools] Serveurs MCP ({MCP_CONFIG.relative_to(MCP_CONFIG.parent.parent)})")
        result = target.run_sync(args.question, model=model)
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except (AgentRunError, UserError):
        raise  # Affiche l’erreur d’exécution initiale de l’agent.
    except (MCPError, RuntimeError, OSError) as e:
        # Le serveur n’a pas démarré ou la connexion a échoué.
        print(f"Impossible de se connecter à un serveur MCP: {e}")
        print("Vérifiez la commande ou l’URL du serveur dans app/mcp_servers.json.")
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
