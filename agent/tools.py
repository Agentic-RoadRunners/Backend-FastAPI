"""
LangGraph agent tools for the SafeRoad AI Assistant.

5 tools:
  1. query_graph — Run Cypher on Neo4j (read-only)
  2. get_incident_detail — Fetch incident from .NET API
  3. get_risk_area — Municipality risk summary from KG
  4. get_nearby_incidents — Spatial proximity search
  5. explain_node — Node + neighbors explanation
"""

import logging
import math

import httpx
from langchain_core.tools import tool

from core.config import settings
from db.neo4j_client import get_driver
from kg import queries as kgq

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────

WRITE_KEYWORDS = {"CREATE", "DELETE", "SET", "MERGE", "REMOVE", "DROP", "DETACH"}


def _is_read_only(cypher: str) -> bool:
    """Check that a Cypher query doesn't contain write operations."""
    upper = cypher.upper()
    for kw in WRITE_KEYWORDS:
        # Only check for standalone keywords (not inside strings)
        if kw in upper:
            return False
    return True


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two lat/lon points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _node_to_dict(node) -> dict:
    """Convert a Neo4j node record to a plain dict."""
    if hasattr(node, "data"):
        return node.data()
    if isinstance(node, dict):
        return node
    return dict(node)


# ══════════════════════════════════════════════════════════════
#  Tool 1: query_graph
# ══════════════════════════════════════════════════════════════

@tool
async def query_graph(cypher: str) -> dict:
    """Run a read-only Cypher query on the Neo4j Knowledge Graph and return results.
    Use this for any KG data retrieval: counting incidents, listing categories,
    finding patterns, or exploring relationships.
    Only MATCH/RETURN/WITH/WHERE/ORDER BY/LIMIT queries are allowed.

    Args:
        cypher: A valid Cypher MATCH query. Must be read-only (no CREATE/DELETE/SET/MERGE).
    """
    if not _is_read_only(cypher):
        return {"error": "Only read-only queries are allowed (MATCH/RETURN). No writes permitted."}

    try:
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run(cypher)
            records = await result.data()
        return {"results": records, "count": len(records)}
    except Exception as e:
        logger.error("query_graph failed: %s | query: %s", e, cypher)
        return {"error": f"Cypher query failed: {e}"}


# ══════════════════════════════════════════════════════════════
#  Tool 2: get_incident_detail
# ══════════════════════════════════════════════════════════════

@tool
async def get_incident_detail(incident_id: str) -> dict:
    """Get full details of a specific incident from the .NET backend API.
    Use this when you need detailed information about a single incident,
    including comments, photos, and verification counts.

    Args:
        incident_id: The UUID of the incident to fetch.
    """
    url = f"{settings.dotnet_api_url}/incidents/{incident_id}"
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"API returned status {resp.status_code}"}
    except Exception as e:
        logger.error("get_incident_detail failed for %s: %s", incident_id, e)
        return {"error": f"Failed to fetch incident: {e}"}


# ══════════════════════════════════════════════════════════════
#  Tool 3: get_risk_area
# ══════════════════════════════════════════════════════════════

@tool
async def get_risk_area(municipality_name: str) -> dict:
    """Get the risk summary for a specific municipality from the Knowledge Graph.
    Returns incident count, top categories, risk weight, and connected incidents.

    Args:
        municipality_name: Name of the municipality (e.g., "Kepez Municipality", "Muratpaşa Municipality").
    """
    try:
        driver = await get_driver()
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
               collect(DISTINCT {id: i.id, title: i.title, status: i.status, weight: i.weight})[0..5] AS top_incidents
        """
        async with driver.session() as session:
            result = await session.run(cypher, name=municipality_name)
            records = await result.data()

        if not records:
            return {"error": f"No municipality found matching '{municipality_name}'"}
        return {"municipality": records[0]}
    except Exception as e:
        logger.error("get_risk_area failed for %s: %s", municipality_name, e)
        return {"error": f"Risk area query failed: {e}"}


# ══════════════════════════════════════════════════════════════
#  Tool 4: get_nearby_incidents
# ══════════════════════════════════════════════════════════════

@tool
async def get_nearby_incidents(
    latitude: float,
    longitude: float,
    radius_meters: int = 1000,
) -> dict:
    """Find incidents near a given location within a radius.
    Uses a bounding box approximation then filters by Haversine distance.

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius_meters: Search radius in meters (default 1000).
    """
    # Approximate bounding box (~0.01 degree ≈ 1.1 km)
    delta_lat = radius_meters / 111_000
    delta_lon = radius_meters / (111_000 * math.cos(math.radians(latitude)))

    try:
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run(
                kgq.GET_INCIDENTS_IN_BBOX,
                min_lat=latitude - delta_lat,
                max_lat=latitude + delta_lat,
                min_lon=longitude - delta_lon,
                max_lon=longitude + delta_lon,
                limit=20,
            )
            records = await result.data()

        # Filter by actual Haversine distance
        nearby = []
        for r in records:
            inc = r.get("i", {})
            if isinstance(inc, dict):
                inc_data = inc
            else:
                inc_data = dict(inc)

            inc_lat = inc_data.get("latitude", 0)
            inc_lon = inc_data.get("longitude", 0)
            dist = _haversine(latitude, longitude, inc_lat, inc_lon)
            if dist <= radius_meters:
                nearby.append({
                    **inc_data,
                    "distance_meters": round(dist),
                })

        nearby.sort(key=lambda x: x.get("distance_meters", 0))
        return {"incidents": nearby[:10], "count": len(nearby)}
    except Exception as e:
        logger.error("get_nearby_incidents failed: %s", e)
        return {"error": f"Nearby search failed: {e}"}


# ══════════════════════════════════════════════════════════════
#  Tool 5: explain_node
# ══════════════════════════════════════════════════════════════

@tool
async def explain_node(node_id: str, node_type: str) -> dict:
    """Explain a specific node in the Knowledge Graph by ID and type.
    Returns the node's properties and its immediate neighbors/connections.

    Args:
        node_id: The id of the node to explain.
        node_type: One of "Incident", "Category", "Municipality", "LocationCluster".
    """
    query_map = {
        "Incident": kgq.EXPLAIN_INCIDENT,
        "Category": kgq.EXPLAIN_CATEGORY,
        "Municipality": kgq.EXPLAIN_MUNICIPALITY,
        "LocationCluster": kgq.EXPLAIN_CLUSTER,
    }

    cypher = query_map.get(node_type)
    if not cypher:
        return {"error": f"Unknown node type: {node_type}. Use one of: Incident, Category, Municipality, LocationCluster"}

    try:
        driver = await get_driver()
        async with driver.session() as session:
            result = await session.run(cypher, node_id=node_id)
            records = await result.data()

        if not records:
            return {"error": f"No {node_type} node found with id '{node_id}'"}

        return {"node_type": node_type, "data": records[0]}
    except Exception as e:
        logger.error("explain_node failed for %s/%s: %s", node_type, node_id, e)
        return {"error": f"Explain query failed: {e}"}


# ══════════════════════════════════════════════════════════════
#  Tool 6: get_weather_for_location
# ══════════════════════════════════════════════════════════════

@tool
async def get_weather_for_location(latitude: float, longitude: float) -> dict:
    """Get current weather conditions for a GPS location using OpenWeatherMap.
    Use this when the user asks about flooding, rain, or weather-related road risks.
    Returns temperature, weather description, and whether it is currently raining.

    Args:
        latitude: Latitude of the location (decimal degrees).
        longitude: Longitude of the location (decimal degrees).
    """
    api_key = settings.openweather_api_key
    if not api_key:
        return {"error": "OpenWeatherMap API key not configured (OPENWEATHER_API_KEY)."}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric", "lang": "tr"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return {"error": f"OpenWeatherMap returned status {resp.status_code}"}
        data = resp.json()
        weather_id = data.get("weather", [{}])[0].get("id", 0)
        is_raining = 200 <= weather_id < 700  # thunderstorm, drizzle, rain, snow, atmosphere
        return {
            "temperature_celsius": data.get("main", {}).get("temp"),
            "feels_like_celsius": data.get("main", {}).get("feels_like"),
            "humidity_percent": data.get("main", {}).get("humidity"),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "wind_speed_ms": data.get("wind", {}).get("speed"),
            "is_raining_or_adverse": is_raining,
            "weather_id": weather_id,
            "city_name": data.get("name", ""),
        }
    except Exception as e:
        logger.error("get_weather_for_location failed at (%.4f, %.4f): %s", latitude, longitude, e)
        return {"error": f"Weather fetch failed: {e}"}


# ── Export all tools ─────────────────────────────────────────
ALL_TOOLS = [
    query_graph,
    get_incident_detail,
    get_risk_area,
    get_nearby_incidents,
    explain_node,
    get_weather_for_location,
]
