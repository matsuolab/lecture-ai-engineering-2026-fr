"""Lecture 06 : tests de raccordement du serveur et du client MCP (sans LLM ni clé API).

Démarrer réellement le serveur glossary d’app/mcp_servers.json (stdio), puis vérifier avec TestModel
que les outils sont exposés et appelés via MCP, et que leurs résultats sont renvoyés.
"""

import json

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import MCP_CONFIG, build_mcp_agent

GLOSSARY_TOOL = "glossary_search_glossary"  # Le nom du serveur "glossary" dans la configuration sert de préfixe


def _glossary_only_config(tmp_path):
    """Utiliser uniquement glossary (ne pas démarrer les serveurs externes comme fetch ajoutés en exercice)."""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    assert "glossary" in config["mcpServers"], "Le serveur glossary est requis dans app/mcp_servers.json"
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps({"mcpServers": {"glossary": config["mcpServers"]["glossary"]}}), encoding="utf-8"
    )
    return path


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_glossary_server_exposes_search_tool(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("Liste des outils", model=model)

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert GLOSSARY_TOOL in offered  # Tester l’inclusion pour permettre l’ajout d’outils pendant l’exercice


def test_glossary_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[GLOSSARY_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("Qu’est-ce que LoRA ?", model=model)

    assert [p.tool_name for p in _parts(result, ToolCallPart)] == [GLOSSARY_TOOL]
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == GLOSSARY_TOOL
    assert str(returns[0].content).strip()  # Un résultat de recherche (ou un message « introuvable ») a été renvoyé
    assert result.output
