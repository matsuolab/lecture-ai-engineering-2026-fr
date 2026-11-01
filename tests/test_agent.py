"""Tests de raccordement de l’agent.

TestModel est un faux modèle qui appelle tous les outils enregistrés puis renvoie une réponse factice,
sans appeler de vrai LLM. Il vérifie l’enregistrement et l’appel des outils, puis le retour des résultats
au modèle, sans clé API ni consommation de quota.
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("Qu’est-ce que LoRA ?")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # Tester l’inclusion pour permettre l’ajout d’outils pendant l’exercice

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # Les outils soumis à approbation (requires_approval=True) attendent sans être exécutés et ne renvoient donc pas de valeur
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("Qu’est-ce que RAG ?")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"
