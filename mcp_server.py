"""
SafeRoad MCP Server — exposes Knowledge Graph tools via Model Context Protocol.

Run standalone (stdio transport):
    python mcp_server.py

Use with Claude Desktop:
    See claude_desktop_config.json for configuration.
"""

import json
import math
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastmcp import FastMCP
from db.neo4j_sync_client import get_sync_driver

mcp = FastMCP("saferoad-kg")

WRITE_KEYWORDS = {"CREATE", "DELETE", "SET", "MERGE", "REMOVE", "DROP", "DETACH"}


def _is_read_only(cypher: str) -> bool:
    upper = cypher.upper()
    return not any(kw in upper for kw in WRITE_KEYWORDS)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Tools ────────────────────────────────────────────────────


@mcp.tool()
def query_graph(cypher: str) -> dict:
    """Run a read-only Cypher query on the SafeRoad Neo4j Knowledge Graph.

    Use this for any KG data retrieval: counting incidents, listing categories,
    finding patterns, or exploring relationships between nodes.
    Only MATCH/RETURN/WITH/WHERE/ORDER BY/LIMIT queries are allowed.

    Args:
        cypher: A valid read-only Cypher MATCH query.
    """
    if not _is_read_only(cypher):
        return {"error": "Only read-only queries allowed. No CREATE/DELETE/SET/MERGE."}

    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher)
            records = [dict(r) for r in result]
        return {"results": records[:20], "count": len(records)}
    except Exception as e:
        return {"error": f"Cypher query failed: {e}"}


@mcp.tool()
def get_risk_area(municipality_name: str) -> dict:
    """Get the risk summary for a specific municipality from the Knowledge Graph.

    Returns incident count, top categories, risk weight, and up to 5 top incidents.
    Municipality names follow the pattern "Kepez Municipality", "Muratpaşa Municipality", etc.

    Args:
        municipality_name: Partial or full name of the municipality (case-insensitive).
    """
    cypher = """
    MATCH (m:Municipality)
    WHERE toLower(m.name) CONTAINS toLower($name)
    OPTIONAL MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m)
    OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
    RETURN m.id AS id,
           m.name AS name,
           m.weight AS weight,
           count(DISTINCT i) AS incident_count,
           collect(DISTINCT c.name) AS categories,
           collect(DISTINCT {id: i.id, title: i.title, status: i.status,
                             weight: i.weight})[0..5] AS top_incidents
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher, name=municipality_name)
            records = [dict(r) for r in result]
        if not records:
            return {"error": f"No municipality found matching '{municipality_name}'"}
        return {"municipality": records[0]}
    except Exception as e:
        return {"error": f"Risk area query failed: {e}"}


@mcp.tool()
def get_nearby_incidents(latitude: float, longitude: float, radius_meters: int = 1000) -> dict:
    """Find road incidents near a given GPS coordinate within a radius.

    Uses bounding-box pre-filter then Haversine distance to return accurate results.
    Useful for "what incidents are near location X?" queries.

    Args:
        latitude: Latitude of the center point (decimal degrees).
        longitude: Longitude of the center point (decimal degrees).
        radius_meters: Search radius in meters (default 1000).
    """
    delta_lat = radius_meters / 111_000
    delta_lon = radius_meters / (111_000 * math.cos(math.radians(latitude)))

    bbox_cypher = """
    MATCH (i:Incident)
    WHERE i.latitude >= $min_lat AND i.latitude <= $max_lat
      AND i.longitude >= $min_lon AND i.longitude <= $max_lon
    RETURN i
    ORDER BY i.weight DESC
    LIMIT 20
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(
                bbox_cypher,
                min_lat=latitude - delta_lat,
                max_lat=latitude + delta_lat,
                min_lon=longitude - delta_lon,
                max_lon=longitude + delta_lon,
            )
            records = [dict(r) for r in result]

        nearby = []
        for r in records:
            inc = r.get("i", {})
            inc_data = dict(inc) if not isinstance(inc, dict) else inc
            dist = _haversine(latitude, longitude,
                              inc_data.get("latitude", 0),
                              inc_data.get("longitude", 0))
            if dist <= radius_meters:
                nearby.append({**inc_data, "distance_meters": round(dist)})

        nearby.sort(key=lambda x: x.get("distance_meters", 0))
        return {"incidents": nearby[:10], "count": len(nearby)}
    except Exception as e:
        return {"error": f"Nearby search failed: {e}"}


@mcp.tool()
def get_incident_detail(incident_id: str) -> dict:
    """Get full details of a specific incident node from the Knowledge Graph.

    Returns all properties of the incident including title, description, status,
    location, weight, and connected category and municipality.

    Args:
        incident_id: The UUID of the incident node.
    """
    cypher = """
    MATCH (i:Incident {id: $id})
    OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
    OPTIONAL MATCH (i)-[:IN_MUNICIPALITY]->(m:Municipality)
    OPTIONAL MATCH (i)-[:IN_CLUSTER]->(lc:LocationCluster)
    RETURN i,
           c.name AS category,
           m.name AS municipality,
           lc.id AS cluster_id
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher, id=incident_id)
            records = [dict(r) for r in result]
        if not records:
            return {"error": f"No incident found with id '{incident_id}'"}
        r = records[0]
        incident_data = dict(r.get("i", {}))
        return {
            "incident": incident_data,
            "category": r.get("category"),
            "municipality": r.get("municipality"),
            "cluster_id": r.get("cluster_id"),
        }
    except Exception as e:
        return {"error": f"Incident detail query failed: {e}"}


# ── Resources ────────────────────────────────────────────────


@mcp.resource("resource://saferoad/kg-stats")
def kg_stats() -> str:
    """Knowledge Graph statistics: total node and edge counts, category distribution.

    Returns a JSON summary of graph health and data coverage.
    """
    cypher_counts = """
    MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
    """
    cypher_edges = "MATCH ()-[r]->() RETURN count(r) AS total_edges"
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            node_records = [dict(r) for r in session.run(cypher_counts)]
            edge_records = [dict(r) for r in session.run(cypher_edges)]

        node_counts = {r["label"]: r["count"] for r in node_records if r["label"]}
        total_edges = edge_records[0]["total_edges"] if edge_records else 0
        return json.dumps({
            "node_counts": node_counts,
            "total_nodes": sum(node_counts.values()),
            "total_edges": total_edges,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("resource://saferoad/municipalities")
def municipalities_list() -> str:
    """List all municipalities in the Knowledge Graph with their risk weights.

    Returns a JSON array ordered by risk weight (highest risk first).
    """
    cypher = """
    MATCH (m:Municipality)
    OPTIONAL MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m)
    RETURN m.id AS id, m.name AS name, m.weight AS weight,
           count(i) AS incident_count
    ORDER BY m.weight DESC
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            records = [dict(r) for r in session.run(cypher)]
        return json.dumps(records)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
