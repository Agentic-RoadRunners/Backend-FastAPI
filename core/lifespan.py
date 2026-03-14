"""
FastAPI lifespan context manager.
Handles startup (DB connections, KG build, agent init) and shutdown (cleanup).
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.supabase_client import create_pool, close_pool
from db.neo4j_client import create_driver, close_driver
from kg.builder import build_knowledge_graph

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
      1. Neo4j driver connection
      2. asyncpg connection pool (Supabase)
      3. KG Builder — build graph from Supabase data
      4. LangGraph agent initialization
    Shutdown:
      - Close Neo4j driver and asyncpg pool
    """
    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 Starting SafeRoad AI Service…")

    # 1. Neo4j
    try:
        await create_driver()
        logger.info("✅ Neo4j driver ready")
    except Exception as e:
        logger.error("❌ Neo4j connection failed: %s", e)
        logger.warning("Service will start without Neo4j — KG endpoints will fail")

    # 2. Supabase asyncpg pool
    try:
        await create_pool()
        logger.info("✅ Supabase asyncpg pool ready")
    except Exception as e:
        logger.error("❌ Supabase connection failed: %s", e)
        logger.warning("Service will start without Supabase — KG build skipped")

    # 3. Build Knowledge Graph
    try:
        start = time.time()
        stats = await build_knowledge_graph()
        elapsed = time.time() - start
        logger.info(
            "✅ KG ready: %d nodes, %d relationships (%.1fs)",
            stats.get("nodes", 0),
            stats.get("relationships", 0),
            elapsed,
        )
    except Exception as e:
        logger.error("❌ KG build failed: %s", e)
        logger.warning("KG will be empty — use POST /kg/sync to rebuild")

    # 4. Agent initialization is lazy (built on first request)
    logger.info("✅ LangGraph agent will initialize on first request")

    logger.info("🟢 SafeRoad AI Service started successfully")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Shutting down SafeRoad AI Service…")
    await close_driver()
    await close_pool()
    from db.neo4j_sync_client import close_sync_driver
    close_sync_driver()  # sync — await yok
    logger.info("🔴 SafeRoad AI Service stopped")
