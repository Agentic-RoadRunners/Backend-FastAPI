"""
SafeRoad AI Service — FastAPI Application Entry Point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.lifespan import lifespan
from routers import chat, kg, admin, crew

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="SafeRoad AI Service",
    description="Knowledge Graph & AI Agent service for SafeRoad platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",   # Angular dev
        "http://localhost:3000",   # fallback
        "https://localhost:9001",  # .NET backend (if proxied)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(chat.router, tags=["Chat"])
app.include_router(kg.router, prefix="/kg", tags=["Knowledge Graph"])
app.include_router(admin.router, prefix="/kg", tags=["Admin"])
app.include_router(crew.router)  # prefix="/crew" router içinde tanımlı


# ── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "SafeRoad AI Service"}
