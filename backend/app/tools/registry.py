"""
MCP (Model Context Protocol) Tool Registry.

Provides:
  - Static registration of built-in tools
  - Dynamic loading from external HTTP MCP servers
  - Tool discovery endpoint for agents
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP Tool Descriptor (mirrors MCP spec schema)
# ---------------------------------------------------------------------------
class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: dict
    server_url: Optional[str] = None   # None = local tool
    provider: str = "builtin"


# ---------------------------------------------------------------------------
# MCP Tool Registry (singleton)
# ---------------------------------------------------------------------------
class MCPToolRegistry:
    """Global registry of all available MCP-compatible tools."""

    _tools: dict[str, MCPTool] = {}
    _local_handlers: dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        tool: MCPTool,
        handler: Optional[Callable] = None,
    ) -> None:
        cls._tools[tool.name] = tool
        if handler:
            cls._local_handlers[tool.name] = handler
        logger.info("Registered MCP tool: %s (provider=%s)", tool.name, tool.provider)

    @classmethod
    async def load_from_server(cls, server_url: str) -> list[str]:
        """
        Discover tools from a remote MCP server (GET /tools).
        Returns list of registered tool names.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{server_url}/tools", timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
            names = []
            for item in data.get("tools", []):
                t = MCPTool(
                    name=item["name"],
                    description=item.get("description", ""),
                    input_schema=item.get("inputSchema", {}),
                    server_url=server_url,
                    provider="remote",
                )
                cls.register(t)
                names.append(t.name)
            logger.info("Loaded %d tools from %s", len(names), server_url)
            return names
        except Exception as exc:
            logger.error("Failed to load tools from %s: %s", server_url, exc)
            return []

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    @classmethod
    async def execute(cls, name: str, arguments: dict) -> dict:
        """
        Execute a tool by name.
        Local tools use registered handlers; remote tools call the MCP server.
        """
        tool = cls._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found in registry"}

        if tool.server_url:
            return await cls._call_remote(tool.server_url, name, arguments)
        else:
            handler = cls._local_handlers.get(name)
            if not handler:
                return {"error": f"No handler for local tool '{name}'"}
            try:
                result = await handler(**arguments)
                return {"result": result}
            except Exception as exc:
                return {"error": str(exc)}

    @classmethod
    async def _call_remote(cls, server_url: str, name: str, arguments: dict) -> dict:
        """POST /tools/{name}/execute to a remote MCP server."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{server_url}/tools/{name}/execute",
                    json={"arguments": arguments},
                    timeout=30.0,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    @classmethod
    def list_tools(cls) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "provider": t.provider,
                "input_schema": t.input_schema,
            }
            for t in cls._tools.values()
        ]

    @classmethod
    def get_tool(cls, name: str) -> Optional[MCPTool]:
        return cls._tools.get(name)


# ---------------------------------------------------------------------------
# Register built-in tools on module load
# ---------------------------------------------------------------------------
def _register_builtins() -> None:
    from app.agents.tools import BUILTIN_TOOLS, execute_tool

    for tool_spec in BUILTIN_TOOLS:
        async def _make_handler(ts=tool_spec):
            async def handler(**kwargs):
                return await ts.fn(**kwargs)
            return handler

        import asyncio
        loop = asyncio.get_event_loop()

        mcp_tool = MCPTool(
            name=tool_spec.name,
            description=tool_spec.description,
            input_schema=tool_spec.parameters,
            provider="builtin",
        )

        async def _handler_factory(ts=tool_spec):
            async def _h(**kwargs):
                return await ts.fn(**kwargs)
            return _h

        # We register without a handler and rely on execute_tool dispatcher
        MCPToolRegistry.register(mcp_tool)


_register_builtins()
