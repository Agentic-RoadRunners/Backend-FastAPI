"""
Pre-built Cypher query templates for the Knowledge Graph.
Used by routers and agent tools.
"""

# ── Full Graph ───────────────────────────────────────────────

GET_ALL_NODES = """
MATCH (n)
RETURN n, labels(n) AS labels
"""

GET_ALL_EDGES = """
MATCH (a)-[r]->(b)
RETURN a.id AS source, b.id AS target, type(r) AS relationship
"""

# ── Node Lookups ─────────────────────────────────────────────

GET_NODE_BY_ID = """
MATCH (n {id: $node_id})
OPTIONAL MATCH (n)-[r]-(neighbor)
RETURN n, labels(n) AS labels,
       collect(DISTINCT {
         id: neighbor.id,
         label: COALESCE(neighbor.title, neighbor.name, neighbor.id),
         type: labels(neighbor)[0],
         relationship: type(r)
       }) AS neighbors
"""

GET_INCIDENTS_BY_STATUS = """
MATCH (i:Incident)
WHERE i.status = $status
RETURN i ORDER BY i.weight DESC
LIMIT $limit
"""

GET_INCIDENTS_BY_CATEGORY = """
MATCH (i:Incident)-[:BELONGS_TO]->(c:Category {name: $category_name})
RETURN i ORDER BY i.weight DESC
LIMIT $limit
"""

# ── Risk Areas ───────────────────────────────────────────────

GET_MUNICIPALITIES_WITH_RISK = """
MATCH (m:Municipality)
OPTIONAL MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m)
WITH m,
     count(i) AS incident_count,
     collect(DISTINCT i.status) AS statuses
OPTIONAL MATCH (i2:Incident)-[:IN_MUNICIPALITY]->(m)
OPTIONAL MATCH (i2)-[:BELONGS_TO]->(c:Category)
WITH m, incident_count, statuses,
     collect(DISTINCT c.name) AS categories
RETURN m.id AS id,
       m.name AS name,
       m.weight AS weight,
       incident_count,
       categories[0..3] AS top_categories
ORDER BY m.weight DESC
"""

# ── Nearby Incidents ─────────────────────────────────────────
# Neo4j Community doesn't have spatial index, so we use a bounding box
# approximation with lat/lon properties, then Haversine in application layer.

GET_INCIDENTS_IN_BBOX = """
MATCH (i:Incident)
WHERE i.latitude >= $min_lat AND i.latitude <= $max_lat
  AND i.longitude >= $min_lon AND i.longitude <= $max_lon
RETURN i
ORDER BY i.weight DESC
LIMIT $limit
"""

# ── Search / General ─────────────────────────────────────────

SEARCH_INCIDENTS_BY_TEXT = """
MATCH (i:Incident)
WHERE toLower(i.title) CONTAINS toLower($query)
   OR toLower(i.description) CONTAINS toLower($query)
RETURN i
ORDER BY i.weight DESC
LIMIT $limit
"""

GET_CATEGORY_STATS = """
MATCH (c:Category)
OPTIONAL MATCH (i:Incident)-[:BELONGS_TO]->(c)
RETURN c.name AS name, c.weight AS weight, count(i) AS incident_count
ORDER BY c.weight DESC
"""

GET_CLUSTER_INFO = """
MATCH (lc:LocationCluster {id: $cluster_id})
OPTIONAL MATCH (i:Incident)-[:IN_CLUSTER]->(lc)
RETURN lc, collect(i) AS incidents
"""

# ── Explain Node ─────────────────────────────────────────────

EXPLAIN_INCIDENT = """
MATCH (i:Incident {id: $node_id})
OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
OPTIONAL MATCH (i)-[:IN_MUNICIPALITY]->(m:Municipality)
OPTIONAL MATCH (i)-[:IN_CLUSTER]->(lc:LocationCluster)
RETURN i, c, m, lc
"""

EXPLAIN_CATEGORY = """
MATCH (c:Category {id: $node_id})
OPTIONAL MATCH (i:Incident)-[:BELONGS_TO]->(c)
RETURN c,
       count(i) AS incident_count,
       collect(i.id)[0..5] AS sample_incident_ids
"""

EXPLAIN_MUNICIPALITY = """
MATCH (m:Municipality {id: $node_id})
OPTIONAL MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m)
OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
RETURN m,
       count(DISTINCT i) AS incident_count,
       collect(DISTINCT c.name) AS categories,
       collect(DISTINCT i.id)[0..5] AS sample_incident_ids
"""

EXPLAIN_CLUSTER = """
MATCH (lc:LocationCluster {id: $node_id})
OPTIONAL MATCH (i:Incident)-[:IN_CLUSTER]->(lc)
OPTIONAL MATCH (lc)<-[:CONTAINS]-(m:Municipality)
RETURN lc, m.name AS municipality_name,
       count(i) AS incident_count,
       collect(i.id)[0..5] AS sample_incident_ids
"""
