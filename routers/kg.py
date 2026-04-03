"""
Knowledge Graph API endpoints.
GET /kg/graph — Full graph data for D3.js frontend
GET /kg/risk-areas — Municipality risk assessments
POST /kg/explain — AI-powered node explanation
"""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_user
from db.neo4j_client import get_driver
from kg import queries
from kg.builder import get_last_sync_stats
from kg.schemas import (
    GraphEdge,
    GraphMetadata,
    GraphNode,
    GraphResponse,
    MunicipalityRisk,
    RiskAreasResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _make_serializable(value):
    """Convert neo4j temporal/spatial types to JSON-safe Python types."""
    if hasattr(value, 'iso_format'):   # neo4j DateTime, Date, Time
        return value.iso_format()
    return value

# ── Simple in-memory cache ───────────────────────────────────
_graph_cache: dict = {"data": None, "timestamp": 0}
CACHE_TTL_SECONDS = 60


def _risk_level(weight: float, max_weight: float) -> str:
    """Map normalised weight to a risk level string."""
    if max_weight <= 0:
        return "low"
    normalised = weight / max_weight
    if normalised >= 0.75:
        return "critical"
    elif normalised >= 0.50:
        return "high"
    elif normalised >= 0.25:
        return "medium"
    return "low"


# ══════════════════════════════════════════════════════════════
#  GET /kg/graph
# ══════════════════════════════════════════════════════════════

@router.get("/graph", response_model=GraphResponse)
async def get_graph(user: dict = Depends(get_current_user)):
    """Return the full knowledge graph for D3.js visualisation."""
    now = time.time()
    if _graph_cache["data"] and (now - _graph_cache["timestamp"]) < CACHE_TTL_SECONDS:
        return _graph_cache["data"]

    try:
        driver = await get_driver()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j not available",
        )

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    async with driver.session() as session:
        # Nodes
        result = await session.run(queries.GET_ALL_NODES)
        records = await result.data()
        for record in records:
            n = record["n"]
            labels = record["labels"]
            node_type = labels[0] if labels else "Unknown"
            node_id = n.get("id", "")
            label = n.get("title") or n.get("name") or node_id

            props = {k: _make_serializable(v) for k, v in dict(n).items()}
            props.pop("id", None)

            nodes.append(
                GraphNode(
                    id=node_id,
                    label=label,
                    type=node_type,
                    weight=n.get("weight", 0),
                    properties=props,
                )
            )

        # Edges
        result = await session.run(queries.GET_ALL_EDGES)
        records = await result.data()
        for record in records:
            edges.append(
                GraphEdge(
                    source=record["source"],
                    target=record["target"],
                    relationship=record["relationship"],
                )
            )

    sync_stats = get_last_sync_stats()
    node_counts: dict[str, int] = {}
    for n in nodes:
        node_counts[n.type] = node_counts.get(n.type, 0) + 1

    metadata = GraphMetadata(
        total_nodes=len(nodes),
        total_edges=len(edges),
        last_sync=sync_stats.get("last_sync", datetime.now(timezone.utc).isoformat()),
        node_counts=node_counts,
    )

    response = GraphResponse(nodes=nodes, edges=edges, metadata=metadata)

    # Cache the result
    _graph_cache["data"] = response
    _graph_cache["timestamp"] = time.time()

    return response


# ══════════════════════════════════════════════════════════════
#  GET /kg/risk-areas
# ══════════════════════════════════════════════════════════════

@router.get("/risk-areas", response_model=RiskAreasResponse)
async def get_risk_areas(user: dict = Depends(get_current_user)):
    """Return risk levels for all municipalities."""
    try:
        driver = await get_driver()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j not available",
        )

    async with driver.session() as session:
        result = await session.run(queries.GET_MUNICIPALITIES_WITH_RISK)
        records = await result.data()

    if not records:
        return RiskAreasResponse(municipalities=[])

    max_weight = max(r.get("weight", 0) or 0 for r in records)

    municipalities = []
    for r in records:
        weight = r.get("weight", 0) or 0
        municipalities.append(
            MunicipalityRisk(
                id=str(r["id"]),
                name=r["name"],
                weight=weight,
                incident_count=r.get("incident_count", 0),
                top_categories=r.get("top_categories", []),
                risk_level=_risk_level(weight, max_weight),
            )
        )

    return RiskAreasResponse(municipalities=municipalities)


# ══════════════════════════════════════════════════════════════
#  POST /kg/explain
# ══════════════════════════════════════════════════════════════

@router.post("/explain")
async def explain_node(
    request: dict,
    user: dict = Depends(get_current_user),
):
    """
    AI-powered explanation of a specific knowledge graph node.
    Delegates to the LangGraph agent's explain_node tool.
    """
    node_id = request.get("node_id")
    node_type = request.get("node_type")

    if not node_id or not node_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="node_id and node_type are required",
        )

    # Import agent lazily to avoid circular imports
    from agent.graph import get_agent
    from langchain_core.messages import HumanMessage

    agent = get_agent()

    prompt = (
        f"Explain the {node_type} node with id '{node_id}'. "
        "Describe what it represents, its weight/importance, and its connections "
        "to other nodes in the knowledge graph. Be concise (2-4 sentences)."
    )

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
    )

    messages = result.get("messages", [])
    answer = messages[-1].content if messages else "No explanation available."

    # Extract related node IDs from tool calls
    highlight_ids = result.get("highlight_ids", [])
    related_nodes = result.get("related_node_ids", [])

    return {
        "explanation": answer,
        "related_nodes": related_nodes,
        "highlight_ids": highlight_ids,
    }
