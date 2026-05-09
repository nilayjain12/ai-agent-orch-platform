"""
Tests for app.core.runtime — the LangGraph orchestration engine.
Covers: _try_parse_failed_tool_call, create_condition_node, get_llm, create_agent_node.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage


# ── Helpers ──────────────────────────────────────────────────

class MockTool:
    """A mock tool whose invoke() always succeeds."""
    def invoke(self, args):
        return f"mock_result_for_{args}"


class FailingTool:
    """A mock tool whose invoke() always raises."""
    def invoke(self, args):
        raise RuntimeError("tool exploded")


MOCK_TOOLS = {"web_search": MockTool(), "calculator": MockTool()}


# ═══════════════════════════════════════════════════════════════
#  _try_parse_failed_tool_call
# ═══════════════════════════════════════════════════════════════

class TestTryParseFailedToolCall:
    """Unit tests for the malformed-tool-call recovery parser."""

    def _parse(self, content, tools=None):
        from app.core.runtime import _try_parse_failed_tool_call
        return _try_parse_failed_tool_call(content, tools or MOCK_TOOLS)

    # ── Pattern 1: <function=name>{...} ──

    def test_pattern1_function_xml(self):
        result = self._parse('<function=web_search>{"query": "AI news"}</function>')
        assert result is not None and "mock_result" in result

    def test_pattern1_with_trailing_semicolon(self):
        result = self._parse('<function=web_search>{"query": "test"};</function>')
        assert result is not None

    # ── Pattern 2: <tool_name>{...} ──

    def test_pattern2_tool_name_tag(self):
        result = self._parse('<web_search>{"query": "test"}</web_search>')
        assert result is not None

    # ── Pattern 3: _TASK={...} ──

    def test_pattern3_task_with_query(self):
        result = self._parse('_TASK={"query": "python tutorials"}')
        assert result is not None

    def test_pattern3_task_with_task_name(self):
        result = self._parse('_TASK={"task_name": "latest AI news"}')
        assert result is not None

    def test_pattern3_task_with_topic(self):
        result = self._parse('_TASK={"topic": "climate change"}')
        assert result is not None

    def test_pattern3_invalid_json_returns_none(self):
        assert self._parse('_TASK={invalid}') is None

    def test_pattern3_empty_query_returns_none(self):
        assert self._parse('_TASK={"query": ""}') is None

    # ── JSON fallback (single quotes → double quotes) ──

    def test_single_quote_json_fallback(self):
        result = self._parse("<function=web_search>{'query': 'test'}</function>")
        assert result is not None

    # ── Negative / edge cases ──

    def test_no_pattern_returns_none(self):
        assert self._parse("Just a normal AI response.") is None

    def test_unknown_tool_returns_none(self):
        assert self._parse('<function=unknown_tool>{"q": "x"}</function>') is None

    def test_completely_invalid_json_returns_none(self):
        assert self._parse("<function=web_search>not json</function>") is None

    def test_tool_invoke_exception_returns_none(self):
        tools = {"web_search": FailingTool()}
        assert self._parse('<function=web_search>{"query": "x"}</function>', tools) is None


# ═══════════════════════════════════════════════════════════════
#  create_condition_node
# ═══════════════════════════════════════════════════════════════

class TestCreateConditionNode:

    def _make(self, node_id, condition):
        from app.core.runtime import create_condition_node
        return create_condition_node(node_id, condition)

    def _state(self, content):
        return {"messages": [HumanMessage(content=content)], "context": {}}

    def test_contains_true(self):
        fn = self._make("c1", "contains 'urgent'")
        assert fn(self._state("This is urgent!"))["context"]["condition_c1"] is True

    def test_contains_false(self):
        fn = self._make("c1", "contains 'urgent'")
        assert fn(self._state("All good"))["context"]["condition_c1"] is False

    def test_is_exact_match_true(self):
        fn = self._make("c2", "is 'hello'")
        assert fn(self._state("hello"))["context"]["condition_c2"] is True

    def test_is_exact_match_false(self):
        fn = self._make("c2", "is 'hello'")
        assert fn(self._state("goodbye"))["context"]["condition_c2"] is False

    def test_fallback_keyword_search(self):
        fn = self._make("c3", "error")
        assert fn(self._state("an error occurred"))["context"]["condition_c3"] is True


# ═══════════════════════════════════════════════════════════════
#  get_llm
# ═══════════════════════════════════════════════════════════════

class TestGetLlm:

    def test_missing_key_raises(self):
        from app.core.runtime import get_llm
        old = os.environ.pop("GROQ_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                get_llm("llama-3.1-8b-instant")
        finally:
            if old:
                os.environ["GROQ_API_KEY"] = old

    def test_valid_key_returns_llm(self):
        from app.core.runtime import get_llm
        os.environ["GROQ_API_KEY"] = "test-key"
        llm = get_llm("llama-3.1-8b-instant", 0.5)
        assert llm is not None


# ═══════════════════════════════════════════════════════════════
#  create_agent_node
# ═══════════════════════════════════════════════════════════════

def _make_agent(**overrides):
    from app.db.models import Agent
    defaults = dict(id=1, name="TestAgent", model_name="llama-3.1-8b-instant",
                    tools=[], temperature="0.7", system_prompt="You are helpful.")
    defaults.update(overrides)
    return Agent(**defaults)


def _make_response(content="OK", tokens=10, tool_calls=None):
    r = MagicMock()
    r.content = content
    r.tool_calls = tool_calls or []
    r.usage_metadata = {"total_tokens": tokens}
    return r


class TestCreateAgentNode:

    @patch("app.core.runtime.get_llm")
    def test_normal_response(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_response("Sunny today", 42)
        mock_llm.bind_tools.return_value = mock_llm
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(), "n1")
        res = fn({"messages": [HumanMessage(content="Hi")], "sender": "user", "context": {}})

        assert res["sender"] == "n1"
        assert res["context"]["tokens"] == 42

    @patch("app.core.runtime.get_llm")
    def test_no_usage_metadata(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        r = MagicMock()
        r.content = "Hi"
        r.tool_calls = []
        r.usage_metadata = None
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = r
        mock_llm.bind_tools.return_value = mock_llm
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(), "n1")
        res = fn({"messages": [HumanMessage(content="x")], "sender": "user", "context": {}})
        assert res["context"]["tokens"] == 0

    @patch("app.core.runtime.AVAILABLE_TOOLS", {"web_search": MockTool()})
    @patch("app.core.runtime.get_llm")
    def test_malformed_content_triggers_manual_fallback(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        malformed = _make_response('<function=web_search>{"query":"x"}</function>', 5)
        summary = _make_response("Here is the summary", 10)
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [malformed, summary]
        mock_llm.bind_tools.return_value = mock_llm
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(tools=["web_search"]), "n1")
        res = fn({"messages": [HumanMessage(content="search")], "sender": "user", "context": {}})
        assert res["sender"] == "n1"

    @patch("app.core.runtime.AVAILABLE_TOOLS", {"web_search": MockTool()})
    @patch("app.core.runtime.get_llm")
    def test_tool_use_failed_exception_recovers(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        mock_llm_tools = MagicMock()
        mock_llm_tools.invoke.side_effect = Exception(
            'tool_use_failed: <function=web_search>{"query":"x"}</function>'
        )
        summary = _make_response("Summary", 15)
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm_tools
        mock_llm.invoke.return_value = summary
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(tools=["web_search"]), "n1")
        res = fn({"messages": [HumanMessage(content="x")], "sender": "user", "context": {}})
        assert res["sender"] == "n1"

    @patch("app.core.runtime.get_llm")
    def test_non_tool_exception_reraises(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = ConnectionError("Network down")
        mock_llm.bind_tools.return_value = mock_llm
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(), "n1")
        with pytest.raises(ConnectionError):
            fn({"messages": [HumanMessage(content="x")], "sender": "user", "context": {}})

    @patch("app.core.runtime.AVAILABLE_TOOLS", {"web_search": MockTool()})
    @patch("app.core.runtime.get_llm")
    def test_tool_failed_manual_also_fails_uses_fallback_llm(self, mock_get_llm):
        from app.core.runtime import create_agent_node
        mock_llm_tools = MagicMock()
        mock_llm_tools.invoke.side_effect = Exception("tool_use_failed: unparseable junk")
        fallback = _make_response("Fallback answer", 8)
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm_tools
        mock_llm.invoke.return_value = fallback
        mock_get_llm.return_value = mock_llm

        fn = create_agent_node(_make_agent(tools=["web_search"]), "n1")
        res = fn({"messages": [HumanMessage(content="x")], "sender": "user", "context": {}})
        assert res["messages"][0].content == "Fallback answer"
