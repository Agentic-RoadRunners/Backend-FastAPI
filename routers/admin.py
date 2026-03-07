"""
Admin-only KG management endpoints.
POST /kg/sync — Full KG rebuild (Admin role required)
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import require_admin
from kg.builder import rebuild_knowledge_graph
from kg.schemas import SyncResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sync", response_model=SyncResponse)
async def sync_knowledge_graph(admin: dict = Depends(require_admin)):
    """
    Completely rebuild the Knowledge Graph.
    Clears Neo4j, re-extracts from Supabase, reloads everything.
    Requires Admin role.
    """
    logger.info("KG sync requested by admin: %s", admin.get("email"))

    start_ms = time.time()
    try:
        stats = await rebuild_knowledge_graph()
    except Exception as e:
        logger.error("KG sync failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KG sync failed: {e}",
        )
    duration_ms = int((time.time() - start_ms) * 1000)

    # Invalidate graph cache
    from routers.kg import _graph_cache
    _graph_cache["data"] = None
    _graph_cache["timestamp"] = 0

    return SyncResponse(
        success=True,
        nodes_created=stats.get("nodes", 0),
        edges_created=stats.get("relationships", 0),
        duration_ms=duration_ms,
        message=(
            f"KG rebuilt: {stats.get('nodes', 0)} nodes, "
            f"{stats.get('relationships', 0)} relationships in {duration_ms}ms"
        ),
    )
