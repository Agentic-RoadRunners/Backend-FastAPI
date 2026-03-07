"""
LangGraph StateGraph definition for the SafeRoad AI Agent.

Single ReAct agent with tool-calling loop:
  call_model → (tool calls?) → tool_node → call_model → … → END

Max 5 iterations to protect token budget.
"""

import logging
from typing import Annotated

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agent.prompts import SYSTEM_PROMPT
from agent.tools import ALL_TOOLS
from core.config import settings

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5

# ── Agent State ──────────────────────────────────────────────


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    highlight_ids: list[str]
    related_node_ids: list[str]
    tool_calls_made: list[str]
    iteration_count: int


# ── Graph Builder ────────────────────────────────────────────

_compiled_graph = None


def _build_agent_graph():
    """Build and compile the LangGraph StateGraph."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0,
        max_tokens=1000,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    # ── Node: call_model ─────────────────────────────────────
    async def call_model(state: AgentState) -> dict:
        messages = state["messages"]

        # Inject system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = await llm_with_tools.ainvoke(messages)

        # Track tool calls
        tool_calls_made = state.get("tool_calls_made", [])
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls_made.append(tc["name"])

        iteration_count = state.get("iteration_count", 0) + 1

        return {
            "messages": [response],
            "tool_calls_made": tool_calls_made,
            "iteration_count": iteration_count,
        }

    # ── Conditional edge: should_continue ────────────────────
    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        iteration = state.get("iteration_count", 0)

        # Guard: max iterations
        if iteration >= MAX_ITERATIONS:
            logger.warning("Agent hit max iterations (%d), forcing END", MAX_ITERATIONS)
            return "end"

        # If the LLM made tool calls, route to tools
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "end"

    # ── Build graph ──────────────────────────────────────────
    graph = StateGraph(AgentState)

    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    graph.add_edge("tools", "agent")

    return graph.compile()


def get_agent():
    """Return the compiled agent graph (singleton, lazy init)."""
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Building LangGraph agent…")
        _compiled_graph = _build_agent_graph()
        logger.info("LangGraph agent ready")
    return _compiled_graph
