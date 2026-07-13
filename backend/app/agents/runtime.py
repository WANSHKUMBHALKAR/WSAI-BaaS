"""
LangGraph-based agent runtime.

Architecture:
  user_input → [memory enrichment] → [LLM node] → [tool call?] → [tool execution] → [LLM node] → response
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from app.agents.tools import get_tool_registry, execute_tool
from app.services.ai_gateway.base import ChatMessage
from app.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: list
    agent_id: str
    user_id: str
    model: str
    system_prompt: str
    max_iterations: int
    iteration: int
    final_response: Optional[str]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
async def _llm_node(state: AgentState) -> AgentState:
    """Call the LLM with current messages and bound tools."""
    from app.core.config import settings

    registry = get_tool_registry()
    tools = [t.to_langchain_tool() for t in registry.values()]

    llm = ChatGoogleGenerativeAI(
        model=state["model"],
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=2048,
    ).bind_tools(tools)

    response = await llm.ainvoke(state["messages"])
    state["messages"].append(response)

    # If no tool calls, we're done
    if not getattr(response, "tool_calls", None):
        state["final_response"] = response.content
    return state


async def _tool_node(state: AgentState) -> AgentState:
    """Execute any tool calls requested by the LLM."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    for tc in tool_calls:
        name = tc["name"]
        args = tc["args"]
        logger.info("Agent %s executing tool: %s(%s)", state["agent_id"], name, args)
        result = await execute_tool(name, args)
        state["messages"].append(
            ToolMessage(content=result, tool_call_id=tc["id"])
        )

    state["iteration"] += 1
    return state


def _should_continue(state: AgentState) -> str:
    """Router: keep looping until done or max iterations reached."""
    last = state["messages"][-1]
    has_tool_calls = bool(getattr(last, "tool_calls", None))
    if has_tool_calls and state["iteration"] < state["max_iterations"]:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("llm", _llm_node)
    graph.add_node("tools", _tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile()


# ---------------------------------------------------------------------------
# Agent Runtime
# ---------------------------------------------------------------------------
class AgentRuntime:
    """
    High-level interface to run a single-agent or multi-turn conversation.
    """

    _graph = None

    def __init__(
        self,
        agent_id: str,
        user_id: str,
        model: str = "gemini-pro",
        system_prompt: str = "You are a helpful AI assistant.",
        memory_manager: Optional[MemoryManager] = None,
        max_iterations: int = 10,
    ) -> None:
        self.agent_id = agent_id
        self.user_id = user_id
        self.model = model
        self.system_prompt = system_prompt
        self.memory = memory_manager
        self.max_iterations = max_iterations

        if AgentRuntime._graph is None:
            AgentRuntime._graph = build_agent_graph()

    async def run(self, user_input: str) -> dict:
        """Execute a full agent loop and return the final response."""
        # 1. Optionally enrich system prompt with memory context
        if self.memory:
            memory_context = await self.memory.get_relevant_context(user_input)
            await self.memory.add_short_term("user", user_input)
            enriched_prompt = self.system_prompt
            if memory_context:
                enriched_prompt += f"\n\n{memory_context}"
        else:
            enriched_prompt = self.system_prompt

        # 2. Build initial state
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content=enriched_prompt),
                HumanMessage(content=user_input),
            ],
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "model": self.model,
            "system_prompt": enriched_prompt,
            "max_iterations": self.max_iterations,
            "iteration": 0,
            "final_response": None,
        }

        # 3. Run graph
        final_state = await AgentRuntime._graph.ainvoke(initial_state)

        response_text = final_state.get("final_response") or ""

        # 4. Persist to memory
        if self.memory and response_text:
            await self.memory.add_short_term("assistant", response_text)
            # Periodically save important exchanges to long-term memory
            await self.memory.add_long_term(
                content=f"User: {user_input}\nAssistant: {response_text}",
                memory_type="episodic",
                importance=0.6,
            )

        return {
            "response": response_text,
            "iterations": final_state["iteration"],
            "messages": len(final_state["messages"]),
        }
