from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
import threading
from typing import Dict
from sqlalchemy import text

from app.core.config import settings, ensure_production_settings
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

# Structured JSON logging with fallback
try:
    from pythonjsonlogger import jsonlogger

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="WSAI BaaS — AI Backend-as-a-Service Platform",
)


# Simple security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Permissions-Policy"] = "geolocation=()"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


# Basic in-memory rate limiter (per-IP sliding window)
class RateLimiter:
    def __init__(self, calls: int = 60, period: int = 60):
        self.calls = calls
        self.period = period
        self.lock = threading.Lock()
        self.store: Dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            q = self.store.setdefault(key, [])
            # drop old
            while q and q[0] <= now - self.period:
                q.pop(0)
            if len(q) >= self.calls:
                return False
            q.append(now)
            return True

limiter = RateLimiter(calls=300, period=60)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client):
        return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
    return await call_next(request)

# Configure CORS using environment-configured allowlist
allow_origins = settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.exception("HTTP error: %s", exc)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.exception("Validation error: %s", exc)
    return JSONResponse({"detail": exc.errors()}, status_code=422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

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
    # Enforce required production settings
    try:
        ensure_production_settings()
    except Exception as e:
        # Re-raise so the process fails fast in production
        logging.getLogger(__name__).error("Production configuration error: %s", e)
        raise

    Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
def shutdown():
    try:
        # Dispose the SQLAlchemy engine pool gracefully
        engine.dispose()
        logger.info("Engine disposed, shutdown complete")
    except Exception:
        logger.exception("Error during shutdown")


@app.get("/health", tags=["Health"])
def health():
    # Basic app-level health check
    return {"status": "ok", "uptime": time.time()}


@app.get("/live", tags=["Health"])
def live():
    # Liveness probe — application is alive
    return {"status": "alive"}


@app.get("/ready", tags=["Health"])
def ready():
    # Readiness probe — check DB connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.exception("Readiness check failed: %s", e)
        return JSONResponse({"status": "not ready"}, status_code=503)
    return {"status": "ready"}

@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{PREFIX}/docs",
        "status": "ok",
    }
