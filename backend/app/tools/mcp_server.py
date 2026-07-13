"""
MCP Server — exposes WSAI BaaS tools via the Model Context Protocol.

Endpoints follow the MCP 1.0 JSON-RPC over HTTP spec:
  GET  /mcp/tools          → list all tools
  POST /mcp/tools/call     → execute a tool
  GET  /mcp/info           → server metadata
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.tools.registry import MCPToolRegistry

router = APIRouter()


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict = {}


class LoadServerRequest(BaseModel):
    server_url: str


@router.get("/info")
def mcp_info():
    return {
        "name": "wsai-baas-mcp-server",
        "version": "1.0.0",
        "protocol": "MCP/1.0",
        "capabilities": ["tools"],
    }


@router.get("/tools")
def list_mcp_tools():
    return {"tools": MCPToolRegistry.list_tools()}


@router.post("/tools/call")
async def call_mcp_tool(req: ToolCallRequest):
    result = await MCPToolRegistry.execute(name=req.name, arguments=req.arguments)
    return result


@router.post("/tools/load-server")
async def load_remote_server(req: LoadServerRequest):
    """Dynamically load tools from a remote MCP-compatible server."""
    loaded = await MCPToolRegistry.load_from_server(req.server_url)
    return {"loaded_tools": loaded, "count": len(loaded)}
