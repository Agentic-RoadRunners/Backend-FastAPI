"""
Knowledge Graph build pipeline: Extract → Transform → Load.

Reads data from Supabase (PostgreSQL), computes clusters and weights,
and loads everything into Neo4j.
"""

import logging
import math
from datetime import datetime, timezone

from db.supabase_client import get_pool
from db.neo4j_client import get_driver
from kg.weights import (
    incident_weight,
    category_weight,
    municipality_weight,
    cluster_weight,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
CLUSTER_THRESHOLD_METERS = 500


# ── Haversine distance ──────────────────────────────────────
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════
#  EXTRACT — Pull data from Supabase
# ══════════════════════════════════════════════════════════════

async def _extract_incidents(pool) -> list[dict]:
    """Fetch incidents with aggregated verification / photo counts."""
    sql = """
        SELECT
            i."Id"::text                        AS id,
            i."Title"                           AS title,
            i."Description"                     AS description,
            i."Status"                          AS status,
            ST_X(i."Location")                  AS longitude,
            ST_Y(i."Location")                  AS latitude,
            i."CreatedAt"                       AS created_at,
            i."CategoryId"                      AS category_id,
            i."MunicipalityId"                  AS municipality_id,
            i."ReporterUserId"::text            AS reporter_user_id,
            COALESCE(u."TrustScore", 100)       AS reporter_trust_score,
            COALESCE(v.pos, 0)                  AS positive_verifications,
            COALESCE(p.cnt, 0)                  AS photo_count
        FROM "Incidents" i
        JOIN "Users" u ON u."Id" = i."ReporterUserId"
        LEFT JOIN (
            SELECT "IncidentId", COUNT(*) FILTER (WHERE "IsPositive" = true) AS pos
            FROM "Verifications"
            GROUP BY "IncidentId"
        ) v ON v."IncidentId" = i."Id"
        LEFT JOIN (
            SELECT "IncidentId", COUNT(*) AS cnt
            FROM "IncidentPhotos"
            GROUP BY "IncidentId"
        ) p ON p."IncidentId" = i."Id"
    """
    rows = await pool.fetch(sql)
    return [dict(r) for r in rows]


async def _extract_categories(pool) -> list[dict]:
    sql = 'SELECT "Id" AS id, "Name" AS name FROM "IncidentCategories"'
    rows = await pool.fetch(sql)
    return [dict(r) for r in rows]


async def _extract_municipalities(pool) -> list[dict]:
    sql = """
        SELECT
            "Id"                                            AS id,
            "Name"                                          AS name,
            COALESCE(ST_Area("Boundary"::geography) / 1000000.0, 0) AS area_km2
        FROM "Municipalities"
    """
    rows = await pool.fetch(sql)
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
#  TRANSFORM — Compute weights & clusters
# ══════════════════════════════════════════════════════════════

def _compute_incident_weights(incidents: list[dict]) -> list[dict]:
    """Attach computed weight to each incident dict."""
    for inc in incidents:
        inc["weight"] = incident_weight(
            positive_verifications=inc["positive_verifications"],
            reporter_trust_score=inc["reporter_trust_score"],
            status=inc["status"],
            photo_count=inc["photo_count"],
        )
    return incidents


def _compute_category_weights(
    categories: list[dict], incidents: list[dict]
) -> list[dict]:
    """Attach weight (count of open incidents) to each category."""
    open_counts: dict[int, int] = {}
    for inc in incidents:
        if inc["status"] != "Resolved":
            cid = inc["category_id"]
            open_counts[cid] = open_counts.get(cid, 0) + 1

    for cat in categories:
        cat["weight"] = category_weight(open_counts.get(cat["id"], 0))
    return categories


def _compute_municipality_weights(
    municipalities: list[dict], incidents: list[dict]
) -> list[dict]:
    """Attach density-based weight to each municipality."""
    weight_sums: dict[int, float] = {}
    for inc in incidents:
        mid = inc.get("municipality_id")
        if mid is not None:
            weight_sums[mid] = weight_sums.get(mid, 0) + inc.get("weight", 0)

    for mun in municipalities:
        mun["weight"] = municipality_weight(
            incident_weights_sum=weight_sums.get(mun["id"], 0),
            boundary_area_km2=mun.get("area_km2", 0),
        )
    return municipalities


def _build_clusters(incidents: list[dict]) -> list[dict]:
    """
    Simple distance-threshold clustering.
    Assign each incident to the nearest cluster within CLUSTER_THRESHOLD_METERS,
    or create a new cluster.
    """
    clusters: list[dict] = []

    for inc in incidents:
        lat, lon = inc.get("latitude"), inc.get("longitude")
        if lat is None or lon is None:
            continue

        assigned = False
        for cl in clusters:
            dist = _haversine(lat, lon, cl["centroid_lat"], cl["centroid_lon"])
            if dist <= CLUSTER_THRESHOLD_METERS:
                cl["incident_ids"].append(inc["id"])
                cl["weights"].append(inc.get("weight", 0))
                # Recompute centroid as average
                n = len(cl["incident_ids"])
                cl["centroid_lat"] = cl["centroid_lat"] + (lat - cl["centroid_lat"]) / n
                cl["centroid_lon"] = cl["centroid_lon"] + (lon - cl["centroid_lon"]) / n
                assigned = True
                break

        if not assigned:
            clusters.append(
                {
                    "id": f"cluster_{len(clusters) + 1}",
                    "centroid_lat": lat,
                    "centroid_lon": lon,
                    "incident_ids": [inc["id"]],
                    "weights": [inc.get("weight", 0)],
                }
            )

    # Compute cluster-level weight
    for cl in clusters:
        cl["weight"] = cluster_weight(cl["weights"])
        cl["incident_count"] = len(cl["incident_ids"])

    return clusters


def _assign_clusters_to_municipalities(
    clusters: list[dict], incidents: list[dict]
) -> list[dict]:
    """Assign each cluster a municipality_id based on majority of its incidents."""
    inc_mun = {inc["id"]: inc.get("municipality_id") for inc in incidents}

    for cl in clusters:
        mun_votes: dict[int, int] = {}
        for iid in cl["incident_ids"]:
            mid = inc_mun.get(iid)
            if mid is not None:
                mun_votes[mid] = mun_votes.get(mid, 0) + 1
        if mun_votes:
            cl["municipality_id"] = max(mun_votes, key=mun_votes.get)  # type: ignore[arg-type]
        else:
            cl["municipality_id"] = None

    return clusters


# ══════════════════════════════════════════════════════════════
#  LOAD — Write to Neo4j
# ══════════════════════════════════════════════════════════════

async def _clear_graph(driver) -> None:
    """Delete all nodes and relationships."""
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")
    logger.info("Neo4j graph cleared")


async def _create_indexes(driver) -> None:
    """Create indexes for fast lookups."""
    indexes = [
        "CREATE INDEX incident_id IF NOT EXISTS FOR (i:Incident) ON (i.id)",
        "CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)",
        "CREATE INDEX municipality_name IF NOT EXISTS FOR (m:Municipality) ON (m.name)",
        "CREATE INDEX incident_status IF NOT EXISTS FOR (i:Incident) ON (i.status)",
    ]
    async with driver.session() as session:
        for idx in indexes:
            await session.run(idx)
    logger.info("Neo4j indexes ensured")


async def _load_categories(driver, categories: list[dict]) -> int:
    cypher = """
    UNWIND $batch AS cat
    MERGE (c:Category {id: cat.id})
    SET c.name = cat.name,
        c.weight = cat.weight
    """
    async with driver.session() as session:
        batch = [{"id": str(c["id"]), "name": c["name"], "weight": c["weight"]} for c in categories]
        await session.run(cypher, batch=batch)
    return len(categories)


async def _load_municipalities(driver, municipalities: list[dict]) -> int:
    cypher = """
    UNWIND $batch AS mun
    MERGE (m:Municipality {id: mun.id})
    SET m.name = mun.name,
        m.weight = mun.weight,
        m.area_km2 = mun.area_km2
    """
    async with driver.session() as session:
        batch = [
            {
                "id": str(m["id"]),
                "name": m["name"],
                "weight": m["weight"],
                "area_km2": m.get("area_km2", 0),
            }
            for m in municipalities
        ]
        await session.run(cypher, batch=batch)
    return len(municipalities)


async def _load_incidents(driver, incidents: list[dict]) -> int:
    cypher = """
    UNWIND $batch AS inc
    MERGE (i:Incident {id: inc.id})
    SET i.title = inc.title,
        i.description = inc.description,
        i.status = inc.status,
        i.latitude = inc.latitude,
        i.longitude = inc.longitude,
        i.weight = inc.weight,
        i.positiveVerifications = inc.positive_verifications,
        i.photoCount = inc.photo_count,
        i.reporterTrustScore = inc.reporter_trust_score,
        i.createdAt = inc.created_at
    """
    async with driver.session() as session:
        batch = [
            {
                "id": inc["id"],
                "title": inc.get("title", ""),
                "description": inc.get("description", ""),
                "status": inc["status"],
                "latitude": inc.get("latitude", 0),
                "longitude": inc.get("longitude", 0),
                "weight": inc.get("weight", 0),
                "positive_verifications": inc.get("positive_verifications", 0),
                "photo_count": inc.get("photo_count", 0),
                "reporter_trust_score": inc.get("reporter_trust_score", 100),
                "created_at": str(inc.get("created_at", "")),
            }
            for inc in incidents
        ]
        await session.run(cypher, batch=batch)
    return len(incidents)


async def _load_clusters(driver, clusters: list[dict]) -> int:
    cypher = """
    UNWIND $batch AS cl
    MERGE (lc:LocationCluster {id: cl.id})
    SET lc.centroidLat = cl.centroid_lat,
        lc.centroidLon = cl.centroid_lon,
        lc.incidentCount = cl.incident_count,
        lc.weight = cl.weight
    """
    async with driver.session() as session:
        batch = [
            {
                "id": cl["id"],
                "centroid_lat": cl["centroid_lat"],
                "centroid_lon": cl["centroid_lon"],
                "incident_count": cl["incident_count"],
                "weight": cl["weight"],
            }
            for cl in clusters
        ]
        await session.run(cypher, batch=batch)
    return len(clusters)


async def _load_relationships(
    driver,
    incidents: list[dict],
    clusters: list[dict],
) -> int:
    """Create all relationships between nodes."""
    rel_count = 0
    async with driver.session() as session:

        # Incident → Category (BELONGS_TO)
        cypher_cat = """
        UNWIND $batch AS rel
        MATCH (i:Incident {id: rel.incident_id})
        MATCH (c:Category {id: rel.category_id})
        MERGE (i)-[:BELONGS_TO]->(c)
        """
        cat_rels = [
            {"incident_id": inc["id"], "category_id": str(inc["category_id"])}
            for inc in incidents
        ]
        await session.run(cypher_cat, batch=cat_rels)
        rel_count += len(cat_rels)

        # Incident → Municipality (IN_MUNICIPALITY)
        cypher_mun = """
        UNWIND $batch AS rel
        MATCH (i:Incident {id: rel.incident_id})
        MATCH (m:Municipality {id: rel.municipality_id})
        MERGE (i)-[:IN_MUNICIPALITY]->(m)
        """
        mun_rels = [
            {"incident_id": inc["id"], "municipality_id": str(inc["municipality_id"])}
            for inc in incidents
            if inc.get("municipality_id") is not None
        ]
        if mun_rels:
            await session.run(cypher_mun, batch=mun_rels)
        rel_count += len(mun_rels)

        # Incident → LocationCluster (IN_CLUSTER)
        cypher_cl = """
        UNWIND $batch AS rel
        MATCH (i:Incident {id: rel.incident_id})
        MATCH (lc:LocationCluster {id: rel.cluster_id})
        MERGE (i)-[:IN_CLUSTER]->(lc)
        """
        cl_rels = []
        for cl in clusters:
            for iid in cl["incident_ids"]:
                cl_rels.append({"incident_id": iid, "cluster_id": cl["id"]})
        if cl_rels:
            await session.run(cypher_cl, batch=cl_rels)
        rel_count += len(cl_rels)

        # Municipality → LocationCluster (CONTAINS)
        cypher_mun_cl = """
        UNWIND $batch AS rel
        MATCH (m:Municipality {id: rel.municipality_id})
        MATCH (lc:LocationCluster {id: rel.cluster_id})
        MERGE (m)-[:CONTAINS]->(lc)
        """
        mun_cl_rels = [
            {"municipality_id": str(cl["municipality_id"]), "cluster_id": cl["id"]}
            for cl in clusters
            if cl.get("municipality_id") is not None
        ]
        if mun_cl_rels:
            await session.run(cypher_mun_cl, batch=mun_cl_rels)
        rel_count += len(mun_cl_rels)

    return rel_count


# ══════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════

async def build_knowledge_graph() -> dict:
    """
    Full KG build pipeline: Extract → Transform → Load.
    Returns a stats dict with node/relationship counts.
    """
    pool = await get_pool()
    driver = await get_driver()

    # ── Extract ──────────────────────────────────────────────
    logger.info("KG Build: Extracting data from Supabase…")
    incidents = await _extract_incidents(pool)
    categories = await _extract_categories(pool)
    municipalities = await _extract_municipalities(pool)

    logger.info(
        "  Extracted: %d incidents, %d categories, %d municipalities",
        len(incidents),
        len(categories),
        len(municipalities),
    )

    # ── Transform ────────────────────────────────────────────
    logger.info("KG Build: Computing weights and clusters…")
    incidents = _compute_incident_weights(incidents)
    categories = _compute_category_weights(categories, incidents)
    municipalities = _compute_municipality_weights(municipalities, incidents)
    clusters = _build_clusters(incidents)
    clusters = _assign_clusters_to_municipalities(clusters, incidents)

    logger.info("  Computed: %d clusters", len(clusters))

    # ── Load ─────────────────────────────────────────────────
    logger.info("KG Build: Loading into Neo4j…")
    await _clear_graph(driver)

    node_count = 0
    node_count += await _load_categories(driver, categories)
    node_count += await _load_municipalities(driver, municipalities)
    node_count += await _load_incidents(driver, incidents)
    node_count += await _load_clusters(driver, clusters)

    rel_count = await _load_relationships(driver, incidents, clusters)

    await _create_indexes(driver)

    stats = {
        "nodes": node_count,
        "relationships": rel_count,
        "incidents": len(incidents),
        "categories": len(categories),
        "municipalities": len(municipalities),
        "clusters": len(clusters),
        "last_sync": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("KG Build complete: %d nodes, %d relationships", node_count, rel_count)
    return stats


# Store last sync stats for GET endpoints
_last_sync_stats: dict = {}


async def rebuild_knowledge_graph() -> dict:
    """Rebuild KG and cache the stats. Called by POST /kg/sync."""
    global _last_sync_stats
    stats = await build_knowledge_graph()
    _last_sync_stats = stats
    return stats


def get_last_sync_stats() -> dict:
    """Return stats from the last successful KG build."""
    return _last_sync_stats
