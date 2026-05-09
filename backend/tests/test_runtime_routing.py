"""
Tests for compile_workflow — the LangGraph graph builder.
All tests mock get_llm so no real Groq API key is needed.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.db.models import Agent, Workflow


def _mock_llm():
    m = MagicMock()
    m.bind_tools.return_value = m
    return m


@pytest.fixture(autouse=True)
def _patch_llm():
    with patch("app.core.runtime.get_llm", return_value=_mock_llm()):
        yield


# ── Helpers ──────────────────────────────────────────────────

def make_agent(id, name="A", tools=None):
    return Agent(id=id, name=name, model_name="llama-3.1-8b-instant",
                 tools=tools or [], temperature="0.7", system_prompt="test")


def make_workflow(nodes, edges):
    return Workflow(id=1, name="WF", description="test", nodes=nodes, edges=edges)


# ── Tests ────────────────────────────────────────────────────

class TestCompileWorkflow:

    def test_single_agent_no_tools(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"}],
        )
        graph = compile_workflow(wf, [make_agent(1)])
        assert graph is not None

    def test_single_agent_with_tools(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"}],
        )
        graph = compile_workflow(wf, [make_agent(1, tools=["calculator"])])
        assert graph is not None

    def test_two_chained_agents(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}},
                   {"id": "a2", "type": "agent", "data": {"agent_id": 2}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"},
                   {"id": "e2", "source": "a1", "target": "a2"}],
        )
        graph = compile_workflow(wf, [make_agent(1), make_agent(2, "B")])
        assert graph is not None

    def test_agent_with_tools_chained_to_next(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}},
                   {"id": "a2", "type": "agent", "data": {"agent_id": 2}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"},
                   {"id": "e2", "source": "a1", "target": "a2"}],
        )
        graph = compile_workflow(wf, [make_agent(1, tools=["web_search"]), make_agent(2, "B")])
        assert graph is not None

    def test_condition_node_routing(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}},
                   {"id": "c1", "type": "condition", "data": {"condition": "contains 'yes'"}},
                   {"id": "a2", "type": "agent", "data": {"agent_id": 2}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"},
                   {"id": "e2", "source": "a1", "target": "c1"},
                   {"id": "e3", "source": "c1", "target": "a2", "sourceHandle": "true"}],
        )
        graph = compile_workflow(wf, [make_agent(1), make_agent(2, "B")])
        assert graph is not None

    def test_no_trigger_defaults_to_first_agent(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "a1", "type": "agent", "data": {"agent_id": 1}}],
            edges=[],
        )
        graph = compile_workflow(wf, [make_agent(1)])
        assert graph is not None

    def test_trigger_no_outgoing_edge_defaults_first_agent(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}}],
            edges=[],
        )
        graph = compile_workflow(wf, [make_agent(1)])
        assert graph is not None

    def test_empty_workflow_no_agents_raises(self):
        """LangGraph requires at least one node with an edge from START."""
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}}],
            edges=[],
        )
        with pytest.raises(ValueError):
            compile_workflow(wf, [])

    def test_edge_to_nonexistent_target_ignored(self):
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 1}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"},
                   {"id": "e2", "source": "a1", "target": "nonexistent"}],
        )
        graph = compile_workflow(wf, [make_agent(1)])
        assert graph is not None

    def test_agent_missing_from_map_raises(self):
        """When an agent node references an ID not in the agent list, wiring fails."""
        from app.core.runtime import compile_workflow
        wf = make_workflow(
            nodes=[{"id": "t", "type": "trigger", "data": {}},
                   {"id": "a1", "type": "agent", "data": {"agent_id": 999}}],
            edges=[{"id": "e1", "source": "t", "target": "a1"}],
        )
        with pytest.raises((AttributeError, ValueError)):
            compile_workflow(wf, [make_agent(1)])
