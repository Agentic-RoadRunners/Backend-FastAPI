"""
CrewAI Tools — SafeRoad KG Enrichment Crew.

Bu dosyadaki tüm fonksiyonlar SYNCHRONOUS'tur.
Thread pool executor (run_in_executor) içinde çalışırlar.
Sync Neo4j driver kullanırlar (db.neo4j_sync_client).

UYARI: Bu araçları LangGraph agent'ı için KULLANMAYIN.
       LangGraph araçları için agent/tools.py dosyasına bakın.
"""

import json
import logging
import uuid

from crewai.tools import tool

from db.neo4j_sync_client import get_sync_driver

logger = logging.getLogger(__name__)

# Read-only guard — write anahtar kelimelerini engelle
WRITE_KEYWORDS = {"CREATE", "DELETE", "SET", "MERGE", "REMOVE", "DROP", "DETACH"}


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1: Read-only Cypher sorgusu
# ─────────────────────────────────────────────────────────────────────────────

@tool("Neo4j Read Query")
def neo4j_query_tool(cypher: str) -> str:
    """
    Neo4j Knowledge Graph üzerinde read-only Cypher sorgusu çalıştırır.
    Sadece MATCH/RETURN sorguları kabul edilir — yazma operasyonları reddedilir.
    Input: Cypher sorgu string'i
    Output: JSON formatında sonuçlar (maksimum 20 kayıt)
    """
    upper = cypher.upper()
    for kw in WRITE_KEYWORDS:
        if kw in upper:
            return f"ERROR: Write operasyonu yasak. '{kw}' içeren sorgular çalıştırılamaz."

    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher)
            records = [dict(r) for r in result]
            return json.dumps(records[:20], default=str)
    except Exception as e:
        logger.error("neo4j_query_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2: Yakın olayları bul (mekansal)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Find Nearby Incidents")
def find_nearby_incidents_tool(lat: float, lng: float, radius_m: int = 500) -> str:
    """
    Verilen koordinatlara belirli yarıçap içindeki incident'ları getirir.
    Input: lat (float), lng (float), radius_m (int, default 500 metre)
    Output: Yakındaki incident listesi JSON formatında
    """
    cypher = """
    MATCH (i:Incident)
    WHERE i.latitude IS NOT NULL AND i.longitude IS NOT NULL
    WITH i,
         point.distance(
             point({latitude: i.latitude, longitude: i.longitude}),
             point({latitude: $lat, longitude: $lng})
         ) AS dist
    WHERE dist <= $radius
    OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
    RETURN i.id AS id, i.title AS title, i.status AS status,
           i.weight AS weight, i.severity AS severity,
           c.name AS category, dist
    ORDER BY dist
    LIMIT 10
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher, lat=lat, lng=lng, radius=radius_m)
            records = [dict(r) for r in result]
            return json.dumps(records, default=str)
    except Exception as e:
        logger.error("find_nearby_incidents_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3: En yakın cluster bilgisi
# ─────────────────────────────────────────────────────────────────────────────

@tool("Get Cluster Info")
def get_cluster_info_tool(lat: float, lng: float) -> str:
    """
    Verilen koordinata 500 metre içindeki en yakın LocationCluster'ı getirir.
    Input: lat (float), lng (float)
    Output: En yakın cluster bilgisi JSON veya "no cluster found"
    """
    cypher = """
    MATCH (lc:LocationCluster)
    WHERE lc.centroidLat IS NOT NULL AND lc.centroidLon IS NOT NULL
    WITH lc,
         point.distance(
             point({latitude: lc.centroidLat, longitude: lc.centroidLon}),
             point({latitude: $lat, longitude: $lng})
         ) AS dist
    WHERE dist <= 500
    RETURN lc.id AS id, lc.centroidLat AS centroidLat, lc.centroidLon AS centroidLon,
           lc.incidentCount AS incidentCount, lc.weight AS weight, dist
    ORDER BY dist
    LIMIT 1
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher, lat=lat, lng=lng)
            records = [dict(r) for r in result]
            if records:
                return json.dumps(records[0], default=str)
            return "no cluster found"
    except Exception as e:
        logger.error("get_cluster_info_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4: Incident node'unu güncelle (severity / urgency_score)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Neo4j Write — Update Incident")
def neo4j_write_tool(incident_id: str, severity: str, urgency_score: float) -> str:
    """
    Incident node'una severity ve urgency_score değerlerini yazar.
    Input: incident_id (str), severity (str: low/medium/high/critical), urgency_score (float 0.0-1.0)
    Output: "success" veya hata mesajı
    """
    cypher = """
    MATCH (i:Incident {id: $id})
    SET i.severity = $severity,
        i.urgencyScore = $urgency_score,
        i.lastAnalyzed = datetime()
    RETURN i.id AS id
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(
                cypher,
                id=incident_id,
                severity=severity,
                urgency_score=urgency_score,
            )
            record = result.single()
            if record:
                return f"success — incident {incident_id} güncellendi"
            return f"ERROR: incident bulunamadı: {incident_id}"
    except Exception as e:
        logger.error("neo4j_write_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5: Cluster'a bağla veya yeni cluster oluştur
# ─────────────────────────────────────────────────────────────────────────────

@tool("Update or Create Cluster")
def update_cluster_tool(
    incident_id: str,
    cluster_id: str = "",
    lat: float = 0.0,
    lng: float = 0.0,
) -> str:
    """
    Incident'ı mevcut bir LocationCluster'a bağlar veya yeni bir cluster oluşturur.
    cluster_id verilirse mevcut cluster'a bağla ve incidentCount artır.
    cluster_id boş string ise yeni cluster oluştur (lat ve lng zorunlu).
    Input: incident_id (str), cluster_id (str, boş ise yeni oluştur), lat (float), lng (float)
    Output: işlem özeti string
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            if cluster_id:
                # Mevcut cluster'a bağla
                cypher = """
                MATCH (i:Incident {id: $incident_id})
                MATCH (lc:LocationCluster {id: $cluster_id})
                MERGE (i)-[:IN_CLUSTER]->(lc)
                SET lc.incidentCount = lc.incidentCount + 1
                RETURN lc.id AS id
                """
                session.run(cypher, incident_id=incident_id, cluster_id=cluster_id)
                return f"incident {incident_id} cluster'a bağlandı: {cluster_id}"
            else:
                # Yeni cluster oluştur
                new_id = f"cluster_{uuid.uuid4().hex[:8]}"
                cypher = """
                MATCH (i:Incident {id: $incident_id})
                MERGE (lc:LocationCluster {id: $cluster_id})
                SET lc.centroidLat = $lat,
                    lc.centroidLon = $lng,
                    lc.radiusMeters = 500,
                    lc.incidentCount = 1,
                    lc.weight = coalesce(i.weight, 0.0)
                MERGE (i)-[:IN_CLUSTER]->(lc)
                RETURN lc.id AS id
                """
                session.run(
                    cypher,
                    incident_id=incident_id,
                    cluster_id=new_id,
                    lat=lat,
                    lng=lng,
                )
                return f"yeni cluster oluşturuldu: {new_id}"
    except Exception as e:
        logger.error("update_cluster_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6: Municipality weight'ini yeniden hesapla
# ─────────────────────────────────────────────────────────────────────────────

@tool("Update Municipality Weight")
def update_municipality_weight_tool(municipality_id: str) -> str:
    """
    Municipality node'unun weight değerini tüm açık incident'ların toplamından yeniden hesaplar.
    Input: municipality_id (str)
    Output: yeni weight değeri veya hata mesajı
    """
    cypher = """
    MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m:Municipality {id: $id})
    WHERE i.status <> 'Resolved'
    WITH m, sum(coalesce(i.weight, 0.0)) AS total_weight, count(i) AS incident_count
    SET m.weight = total_weight /
        CASE WHEN coalesce(m.areaKm2, 0) > 0 THEN m.areaKm2 ELSE 1 END,
        m.openIncidentCount = incident_count
    RETURN m.weight AS new_weight
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(cypher, id=municipality_id)
            record = result.single()
            if record:
                return f"municipality weight güncellendi: {record['new_weight']:.4f}"
            return f"ERROR: municipality bulunamadı: {municipality_id}"
    except Exception as e:
        logger.error("update_municipality_weight_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 7: SIMILAR_TO ilişkisi oluştur
# ─────────────────────────────────────────────────────────────────────────────

@tool("Create SIMILAR_TO Relationship")
def create_similar_to_tool(
    incident_id: str,
    similar_incident_id: str,
    similarity_score: float,
) -> str:
    """
    İki incident arasında SIMILAR_TO ilişkisi oluşturur (MERGE ile — duplicate olmaz).
    Input: incident_id (kaynak), similar_incident_id (hedef), similarity_score (0.0-1.0)
    Output: işlem sonucu string
    """
    cypher = """
    MATCH (i1:Incident {id: $id1})
    MATCH (i2:Incident {id: $id2})
    MERGE (i1)-[r:SIMILAR_TO]->(i2)
    SET r.similarity_score = $score,
        r.created_at = datetime()
    RETURN i1.id AS source, i2.id AS target
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            result = session.run(
                cypher,
                id1=incident_id,
                id2=similar_incident_id,
                score=similarity_score,
            )
            record = result.single()
            if record:
                return f"SIMILAR_TO ilişkisi kuruldu: {incident_id} → {similar_incident_id} (score={similarity_score})"
            return f"ERROR: incident bulunamadı ({incident_id} veya {similar_incident_id})"
    except Exception as e:
        logger.error("create_similar_to_tool hatası: %s", e)
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Dışa aktarılan gruplar (crew.py'de kullanım için)
# ─────────────────────────────────────────────────────────────────────────────

CREW_READ_TOOLS = [neo4j_query_tool, find_nearby_incidents_tool, get_cluster_info_tool]
CREW_WRITE_TOOLS = [neo4j_write_tool, update_cluster_tool, update_municipality_weight_tool, create_similar_to_tool]
