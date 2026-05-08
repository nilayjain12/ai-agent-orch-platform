import os
import operator
from typing import TypedDict, Annotated, Sequence, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
import json
import logging
import re
from app.core.tools import AVAILABLE_TOOLS
from app.db.models import Agent, Workflow

logger = logging.getLogger(__name__)

# Use the same fast model for tool-calling agents.
# The 8b model sometimes generates broken XML tags (<function=...>) instead of
# proper JSON tool_calls. Our _try_parse_failed_tool_call() function handles
# this by parsing the broken tags and executing the tool manually.
# The 70b-versatile model is more reliable but has very low free-tier rate limits.
TOOL_CALLING_MODEL = "llama-3.1-8b-instant"

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str # Now stores the React Flow Node ID
    context: Dict[str, Any]

def get_llm(model_name: str, temperature: float = 0.7):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return ChatGroq(
        api_key=groq_api_key,
        model_name=model_name,
        temperature=temperature,
    )


def _try_parse_failed_tool_call(content: str, available_tools: dict) -> str | None:
    """
    Parses malformed tool tags in content and executes them manually.
    Handles formats like:
    <function=name>{"arg": "val"}
    <web_search>{"query": "..."}</web_search>
    <weather>{"location": "..."};</function>
    """
    # Pattern 1: <function=name>{"args": ...}
    m1 = re.search(r'<function=(\w+)[^>{]*>?\s*(\{.*?\})', content, re.DOTALL)
    
    # Pattern 2: <tool_name>{"args": ...}
    tool_names = "|".join(available_tools.keys())
    m2 = re.search(rf'<({tool_names})>\s*({{.*?}})', content, re.DOTALL)
    
    match = m1 or m2
    if not match:
        return None

    func_name = match.group(1)
    args_str = match.group(2).strip()
    
    # Clean up trailing semicolons or noise after JSON
    if args_str.endswith(';'):
        args_str = args_str[:-1]

    try:
        args = json.loads(args_str)
    except json.JSONDecodeError:
        return None

    tool_fn = available_tools.get(func_name)
    if not tool_fn:
        return None

    try:
        result = tool_fn.invoke(args)
        logger.info("Manual tool execution OK: %s(%s) -> %s", func_name, args, str(result)[:200])
        return str(result)
    except Exception as e:
        logger.warning("Manual tool execution failed for %s: %s", func_name, str(e))
        return None

def create_agent_node(agent_config: Agent, node_id: str):
    """Factory to create a graph node for a specific agent."""
    agent_tools = [AVAILABLE_TOOLS[t] for t in (agent_config.tools or []) if t in AVAILABLE_TOOLS]
    has_tools = len(agent_tools) > 0
    model_name = TOOL_CALLING_MODEL if has_tools else agent_config.model_name

    llm = get_llm(model_name, float(agent_config.temperature))
    llm_with_tools = llm.bind_tools(agent_tools) if has_tools else llm

    def _handle_manual_result(result, history, model, config):
        synth_messages = history + [
            AIMessage(content="Searching for information..."),
            HumanMessage(content=f"The tool returned the following result: {result}. Please provide a comprehensive summary for the user.")
        ]
        plain_llm = get_llm(model, float(config.temperature))
        response = plain_llm.invoke([SystemMessage(content=config.system_prompt)] + synth_messages)
        return {"messages": [response], "sender": node_id}

    def agent_node(state: AgentState):
        messages = list(state['messages'])
        system_msg = SystemMessage(content=agent_config.system_prompt)

        try:
            response = llm_with_tools.invoke([system_msg] + messages)
            
            # ── Check for malformed tags in successful response content ──
            if not (hasattr(response, "tool_calls") and response.tool_calls):
                content = response.content
                if "<" in content and ("{" in content or "=" in content):
                    tool_result = _try_parse_failed_tool_call(content, AVAILABLE_TOOLS)
                    if tool_result:
                        return _handle_manual_result(tool_result, messages, model_name, agent_config)

            return {"messages": [response], "sender": node_id}

        except Exception as e:
            error_str = str(e)
            tool_result = None
            if "tool_use_failed" in error_str or "failed_generation" in error_str or ("<" in error_str and "{" in error_str):
                logger.warning("Tool call failed or malformed for agent '%s', attempting manual execution.", agent_config.name)
                tool_result = _try_parse_failed_tool_call(error_str, AVAILABLE_TOOLS)

            if tool_result is not None:
                return _handle_manual_result(tool_result, messages, model_name, agent_config)
            
            if "tool_use_failed" not in error_str and "failed_generation" not in error_str:
                raise  # Re-raise non-tool related errors
            
            logger.warning("Manual execution failed; answering without tools.")
            plain_llm = get_llm(model_name, float(agent_config.temperature))
            fallback_prompt = f"{agent_config.system_prompt}\n\nAnswer the user's question directly using your own knowledge."
            response = plain_llm.invoke([SystemMessage(content=fallback_prompt)] + messages)
            return {"messages": [response], "sender": node_id}

    return agent_node


# ─────────────────────────────────────────────────────────────
# Graph Compilation
# ─────────────────────────────────────────────────────────────

def create_condition_node(node_id: str, condition_text: str):
    """Creates a node that evaluates a condition and routes to True/False."""
    def condition_node(state: AgentState):
        last_message = state["messages"][-1].content.lower()
        condition = condition_text.lower()
        
        # Simple evaluation logic: check if keywords exist or if it's a direct match
        result = False
        if "contains" in condition:
            keyword = condition.split("contains")[-1].strip().strip("'").strip('"')
            result = keyword in last_message
        elif "is" in condition:
            val = condition.split("is")[-1].strip().strip("'").strip('"')
            result = val == last_message
        else:
            # Fallback to direct keyword search
            result = condition in last_message
            
        return {"context": {f"condition_{node_id}": result}}
    return condition_node

def compile_workflow(workflow: Workflow, agents: List[Agent]) -> StateGraph:
    """Compiles a LangGraph StateGraph from the Workflow configuration."""
    graph_builder = StateGraph(AgentState)

    agent_map = {a.id: a for a in agents}
    nodes = workflow.nodes
    edges = workflow.edges

    # Collect all tools used by any agent in this workflow
    all_tool_names = set()
    for a in agents:
        if a.tools:
            all_tool_names.update(a.tools)

    tools_list = [AVAILABLE_TOOLS[t] for t in all_tool_names if t in AVAILABLE_TOOLS]
    has_tools = bool(tools_list)

    if has_tools:
        graph_builder.add_node("tools", ToolNode(tools_list))

    # Pre-compute edges for all nodes
    node_outputs: Dict[str, Dict[str, str]] = {} # source_id -> {handle_id or "default": target_node_name}
    for edge in edges:
        src_id = edge["source"]
        tgt_id = edge["target"]
        handle = edge.get("sourceHandle", "default")
        
        target_node = next((n for n in nodes if n["id"] == tgt_id), None)
        if not target_node: continue
        
        target_name = target_node["id"]
        
        if src_id not in node_outputs: node_outputs[src_id] = {}
        node_outputs[src_id][handle] = target_name

    # Create and add all nodes
    graph_node_names = []
    for node in nodes:
        node_id = node["id"]
        if node["type"] == "agent":
            agent_id = node["data"]["agent_id"]
            agent_config = agent_map.get(agent_id)
            if not agent_config: continue
            
            graph_builder.add_node(node_id, create_agent_node(agent_config, node_id))
            graph_node_names.append(node_id)
        
        elif node["type"] == "condition":
            condition_text = node["data"].get("condition", "")
            graph_builder.add_node(node_id, create_condition_node(node_id, condition_text))
            graph_node_names.append(node_id)

    # Wire edges for each node
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        node_name = node_id
        
        if node_type == "agent":
            outputs = node_outputs.get(node_id, {})
            next_target = outputs.get("default")
            
            agent_id = node["data"]["agent_id"]
            agent_config = agent_map.get(agent_id)
            agent_has_tools = bool([t for t in (agent_config.tools or []) if t in AVAILABLE_TOOLS])

            if agent_has_tools and next_target:
                def _router(state: AgentState, _next=next_target):
                    last = state["messages"][-1]
                    if hasattr(last, "tool_calls") and last.tool_calls:
                        return "tools"
                    return _next
                graph_builder.add_conditional_edges(node_name, _router, {"tools": "tools", next_target: next_target})
            elif agent_has_tools:
                graph_builder.add_conditional_edges(node_name, tools_condition, {"tools": "tools", END: END})
            elif next_target:
                graph_builder.add_edge(node_name, next_target)
            else:
                graph_builder.add_edge(node_name, END)
                
        elif node_type == "condition":
            outputs = node_outputs.get(node_id, {})
            true_target = outputs.get("true", END)
            false_target = outputs.get("false", END)
            
            def _condition_router(state: AgentState, _id=node_id, _t=true_target, _f=false_target):
                return _t if state["context"].get(f"condition_{_id}") else _f
                
            graph_builder.add_conditional_edges(node_name, _condition_router, {true_target: true_target, false_target: false_target, END: END})

    # Route tool results back to the calling agent using node ID
    if has_tools:
        def tool_router(state: AgentState):
            sender = state.get("sender", "")
            if sender in graph_node_names:
                return sender
            return graph_node_names[0] if graph_node_names else END
        graph_builder.add_conditional_edges("tools", tool_router)

    # Entry point
    trigger = next((n for n in nodes if n["type"] == "trigger"), None)
    if trigger:
        outputs = node_outputs.get(trigger["id"], {})
        start_target = outputs.get("default")
        if start_target:
            graph_builder.add_edge(START, start_target)
        elif graph_node_names:
            graph_builder.add_edge(START, graph_node_names[0])
    elif graph_node_names:
        graph_builder.add_edge(START, graph_node_names[0])
    else:
        graph_builder.add_edge(START, END)

    return graph_builder.compile()
