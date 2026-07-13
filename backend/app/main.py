from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.auth.router import router as auth_router
from app.api.gateway import router as gateway_router
from app.api.rag import router as rag_router
from app.api.agents import router as agents_router
from app.tools.mcp_server import router as mcp_router
from app.api.memory import router as memory_router
from app.api.workflows import router as workflows_router
from app.api.organizations import router as organizations_router
from app.api.projects import router as projects_router
from app.api.apikeys import router as apikeys_router
from app.api.analytics import router as analytics_router
from app.database.session import Base, engine
from app.models import *

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="WSAI BaaS — AI Backend-as-a-Service Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_V1_STR

app.include_router(auth_router,          prefix=f"{PREFIX}/auth",          tags=["Auth"])
app.include_router(gateway_router,       prefix=f"{PREFIX}/gateway",       tags=["AI Gateway"])
app.include_router(rag_router,           prefix=f"{PREFIX}/rag",           tags=["RAG"])
app.include_router(agents_router,        prefix=f"{PREFIX}/agents",        tags=["Agents"])
app.include_router(mcp_router,           prefix=f"{PREFIX}/mcp",           tags=["MCP"])
app.include_router(memory_router,        prefix=f"{PREFIX}/memory",        tags=["Memory"])
app.include_router(workflows_router,     prefix=f"{PREFIX}/workflows",     tags=["Workflows"])
app.include_router(organizations_router,  prefix=f"{PREFIX}/organizations", tags=["Organizations"])
app.include_router(projects_router,      prefix=f"{PREFIX}/projects",      tags=["Projects"])
app.include_router(apikeys_router,       prefix=f"{PREFIX}/apikeys",       tags=["API Keys"])
app.include_router(analytics_router,     prefix=f"{PREFIX}/analytics",     tags=["Analytics"])



@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{PREFIX}/docs",
        "status": "ok",
    }
