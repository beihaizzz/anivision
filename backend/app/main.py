"""
AniVision — FastAPI Application Entry Point

Anime character image recognition system with community features.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import (
    analytics,
    auth,
    characters,
    posts,
    recognition,
    search,
    users,
)


# ── Application Lifespan ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup: Initialize database tables (for development).
    On shutdown: Cleanup resources.
    """
    # Startup
    try:
        await init_db()
        print("[AniVision] Database tables initialized successfully.")
    except Exception as e:
        print(f"[AniVision] Warning: Could not initialize database: {e}")
        print("[AniVision] The server will still start. Migrations may be needed.")

    yield

    # Shutdown
    print("[AniVision] Server shutting down.")


# ── FastAPI App ───────────────────────────────────────────────────────

app = FastAPI(
    title="AniVision",
    description="动漫角色图像识别系统API — Anime Character Image Recognition System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS Middleware ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ─────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# ── Health Check ──────────────────────────────────────────────────────


@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns the service status and version info.
    """
    return {
        "status": "healthy",
        "service": "AniVision API",
        "version": "1.0.0",
    }

# ── Register Routers ──────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(recognition.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
