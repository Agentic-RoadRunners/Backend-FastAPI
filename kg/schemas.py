"""
Pydantic models for Knowledge Graph API responses.
"""

from pydantic import BaseModel


class GraphNode(BaseModel):
    """A single node in the knowledge graph."""

    id: str
    label: str
    type: str  # "Incident" | "Category" | "Municipality" | "LocationCluster"
    weight: float
    properties: dict  # type-specific extra fields


class GraphEdge(BaseModel):
    """A single edge in the knowledge graph."""

    source: str  # source node id
    target: str  # target node id
    relationship: str  # "BELONGS_TO" | "IN_MUNICIPALITY" | "IN_CLUSTER" | "CONTAINS"


class GraphMetadata(BaseModel):
    """Summary statistics about the graph."""

    total_nodes: int
    total_edges: int
    last_sync: str  # ISO datetime of last KG build
    node_counts: dict  # e.g. {"Incident": 45, "Category": 5, ...}


class GraphResponse(BaseModel):
    """Full graph payload returned by GET /kg/graph."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: GraphMetadata


class MunicipalityRisk(BaseModel):
    """Risk assessment for a single municipality."""

    id: str
    name: str
    weight: float
    incident_count: int
    top_categories: list[str]
    risk_level: str  # "low" | "medium" | "high" | "critical"


class RiskAreasResponse(BaseModel):
    """Response for GET /kg/risk-areas."""

    municipalities: list[MunicipalityRisk]


class SyncResponse(BaseModel):
    """Response for POST /kg/sync."""

    success: bool
    nodes_created: int
    edges_created: int
    duration_ms: int
    message: str
