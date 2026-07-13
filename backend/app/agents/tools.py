"""
Built-in tool library for agents.
Each tool is a callable that takes structured kwargs and returns a string result.
"""
from __future__ import annotations

import json
import logging
from langchain_core.tools import StructuredTool
from typing import Callable, Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool descriptor
# ---------------------------------------------------------------------------
class ToolSpec:
    def __init__(self, name: str, description: str, parameters: dict, fn: Callable) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.fn = fn

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    def to_langchain_tool(self):
        return StructuredTool.from_function(
          func=self.fn,
          name=self.name,
          description=self.description,
        
        )    


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
async def _web_search(query: str) -> str:
    """Search the web using DuckDuckGo Instant Answer API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1"},
                timeout=10.0,
            )
            data = resp.json()
        abstract = data.get("AbstractText", "")
        topics = data.get("RelatedTopics", [])
        results = [abstract] if abstract else []
        for topic in topics[:3]:
            if isinstance(topic, dict):
                results.append(topic.get("Text", ""))
        return "\n".join(results) or "No results found."
    except Exception as exc:
        return f"Search error: {exc}"


async def _calculator(expression: str) -> str:
    """Safely evaluate a math expression."""
    try:
        # Only allow safe characters
        safe_expr = "".join(c for c in expression if c in "0123456789+-*/.() ")
        result = eval(safe_expr)  # noqa: S307
        return str(result)
    except Exception as exc:
        return f"Calculation error: {exc}"


async def _get_current_time() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


async def _http_request(url: str, method: str = "GET", body: str = "") -> str:
    """Make an HTTP request and return the response body (truncated)."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(method.upper(), url, content=body, timeout=15.0)
            return resp.text[:2000]
    except Exception as exc:
        return f"HTTP error: {exc}"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
BUILTIN_TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="web_search",
        description="Search the web for current information about a topic.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
        fn=_web_search,
    ),
    ToolSpec(
        name="calculator",
        description="Evaluate a mathematical expression and return the result.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression to evaluate"}},
            "required": ["expression"],
        },
        fn=_calculator,
    ),
    ToolSpec(
        name="get_current_time",
        description="Get the current UTC date and time.",
        parameters={"type": "object", "properties": {}, "required": []},
        fn=_get_current_time,
    ),
    ToolSpec(
        name="http_request",
        description="Make an HTTP GET or POST request to an external URL.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "body": {"type": "string"},
            },
            "required": ["url"],
        },
        fn=_http_request,
    ),
]


def get_tool_registry() -> dict[str, ToolSpec]:
    return {t.name: t for t in BUILTIN_TOOLS}


async def execute_tool(name: str, arguments: dict) -> str:
    registry = get_tool_registry()
    tool = registry.get(name)
    if not tool:
        return f"Unknown tool: {name}"
    try:
        result = await tool.fn(**arguments)
        return str(result)
    except Exception as exc:
        logger.error("Tool %s failed: %s", name, exc)
        return f"Tool execution error: {exc}"
