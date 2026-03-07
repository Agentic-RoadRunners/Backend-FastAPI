# SafeRoad — FastAPI & Knowledge Graph Service
## Product Requirements Document (PRD)

**Versiyon:** 1.0  
**Tarih:** Mart 2026  
**Proje:** SafeRoad — Community-Based Road Safety Platform  
**Kapsam:** FastAPI AI/KG Servisi — Tasarım & İmplementasyon Rehberi

---

## 1. Genel Bakış

Bu PRD, SafeRoad platformuna entegre edilecek **FastAPI tabanlı AI ve Knowledge Graph servisinin** tam implementasyon gereksinimlerini tanımlar. Servis iki ana sorumluluğu üstlenir:

1. **Knowledge Graph (KG):** Supabase'deki incident verilerinden Neo4j graph'ı inşa etmek, ağırlıklı node hesaplamak ve D3.js frontend'e graph verisi sunmak.
2. **AI Agent:** LangGraph ile orchestrate edilen tek bir ReAct agent'ı; kullanıcının doğal dil sorgularını Cypher sorgularına çevirerek KG üzerinden yanıt üretmek.

---

## 2. Sistem Bağlamı

```
Angular 19 (Frontend)
    │
    ├──► .NET 8 API (localhost:9001)  ──► Supabase PostgreSQL + PostGIS
    │         REST/JSON                        (incidents, users, municipalities)
    │
    └──► FastAPI Service (localhost:8000)
              │
              ├──► Neo4j (In-Memory)       ← Supabase'den sync edilir
              ├──► OpenAI API (GPT-4o-mini)
              └──► LangGraph Agent
```

**Önemli kural:** FastAPI servisi .NET API'ye **doğrudan bağımlı değildir.** Incident verilerini Supabase'den bağımsız olarak okur. Gerektiğinde .NET API'ye tool call yapabilir (incident detail gibi).

---

## 3. Teknoloji Stack

| Katman | Teknoloji | Versiyon | Notlar |
|--------|-----------|----------|--------|
| Web Framework | FastAPI | 0.115+ | Async-first, Pydantic v2 |
| Graph DB | Neo4j | 5.x Community | In-memory, restart'ta rebuild |
| Graph Driver | neo4j-python-driver | 5.x | Bolt protocol |
| DB Bağlantısı | asyncpg | 0.29+ | Supabase'e direkt async bağlantı |
| AI Framework | LangGraph | 0.2+ | ReAct agent orchestration |
| LLM | OpenAI GPT-4o-mini | latest | Tool use destekli |
| Validation | Pydantic | v2 | Request/response modelleri |
| Config | python-dotenv | — | .env yönetimi |
| Testing | pytest + pytest-asyncio | — | Async test desteği |

---

## 4. Proje Klasör Yapısı

```
saferoad-fastapi/
│
├── main.py                    # FastAPI app, lifespan, router kayıtları
├── .env                       # Environment değişkenleri
├── requirements.txt
│
├── core/
│   ├── config.py              # Settings (Pydantic BaseSettings)
│   └── lifespan.py            # Startup/shutdown: KG build + Neo4j bağlantısı
│
├── db/
│   ├── supabase_client.py     # asyncpg bağlantı pool
│   └── neo4j_client.py        # Neo4j driver singleton
│
├── kg/
│   ├── builder.py             # KG inşa pipeline (Extract → Transform → Load)
│   ├── queries.py             # Hazır Cypher sorguları
│   ├── weights.py             # Node ağırlık hesaplama formülleri
│   └── schemas.py             # GraphNode, GraphEdge Pydantic modelleri
│
├── agent/
│   ├── graph.py               # LangGraph StateGraph tanımı
│   ├── tools.py               # Agent tool'ları (5 adet)
│   ├── prompts.py             # System prompt + tool descriptions
│   └── schemas.py             # ChatMessage, AgentResponse modelleri
│
└── routers/
    ├── chat.py                # POST /chat
    ├── kg.py                  # GET /kg/graph, POST /kg/explain, GET /kg/risk-areas
    └── admin.py               # POST /kg/sync (Admin only)
```

---

## 5. Environment Değişkenleri (.env)

```env
# Supabase
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Neo4j (local in-memory instance)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=saferoad_local

# OpenAI
OPENAI_API_KEY=sk-...

# .NET API (bazı tool call'lar için)
DOTNET_API_URL=https://localhost:9001/api

# JWT (Angular'dan gelen token'ları doğrulamak için)
JWT_SECRET=same_secret_as_dotnet
JWT_ALGORITHM=HS256

# App
DEBUG=true
LOG_LEVEL=INFO
```

---

## 6. Startup Lifecycle (lifespan.py)

FastAPI `lifespan` context manager ile uygulama ayağa kalktığında şu sıra çalışır:

```
1. Neo4j driver bağlantısı aç
2. asyncpg connection pool oluştur (Supabase)
3. KG Builder'ı çalıştır:
   a. Supabase'den incidents, categories, municipalities çek
   b. Node ağırlıklarını hesapla
   c. Location cluster'ları oluştur (500m threshold)
   d. Neo4j'e MERGE ile yaz
   e. Index'leri oluştur
4. LangGraph agent'ı initialize et
5. Loglara "KG ready: X nodes, Y relationships" yaz
```

Shutdown'da Neo4j driver ve asyncpg pool kapatılır.

---

## 7. Knowledge Graph — Detaylı Tasarım

### 7.1 Node Tipleri ve Properties

```cypher
// Incident Node
(:Incident {
  id: string,
  title: string,
  description: string,
  status: string,          // "Pending" | "InProgress" | "Resolved"
  latitude: float,
  longitude: float,
  createdAt: datetime,
  weight: float,           // hesaplanmış ağırlık
  photoCount: integer,
  verificationCount: integer,
  reporterTrustScore: float
})

// Category Node
(:Category {
  id: string,
  name: string,            // "Pothole" | "Flooding" | "Accident" | "Roadwork" | "Other"
  weight: float            // o kategorideki açık incident sayısı
})

// Municipality Node
(:Municipality {
  id: string,
  name: string,
  weight: float            // incident yoğunluğu (count / alan km²)
})

// LocationCluster Node
(:LocationCluster {
  id: string,
  centroidLat: float,
  centroidLng: float,
  radiusMeters: float,
  incidentCount: integer,
  weight: float
})
```

### 7.2 Relationship Tipleri

```cypher
(:Incident)-[:BELONGS_TO]->(:Category)
(:Incident)-[:IN_MUNICIPALITY]->(:Municipality)
(:Incident)-[:IN_CLUSTER]->(:LocationCluster)
(:Municipality)-[:CONTAINS]->(:LocationCluster)
```

### 7.3 Node Ağırlık Formülleri (weights.py)

```python
# Incident weight
def incident_weight(positive_verifications, reporter_trust_score, status, photo_count):
    status_multiplier = {"Pending": 1.5, "InProgress": 1.0, "Resolved": 0.3}
    base = positive_verifications * reporter_trust_score
    bonus = 0.1 * photo_count  # fotoğraflı incident biraz daha güvenilir
    return base * status_multiplier.get(status, 1.0) + bonus

# Category weight
def category_weight(open_incident_count):
    return float(open_incident_count)

# Municipality weight (density-based)
def municipality_weight(incident_weights_sum, boundary_area_km2):
    if boundary_area_km2 == 0:
        return 0.0
    return incident_weights_sum / boundary_area_km2

# LocationCluster weight
def cluster_weight(incident_weights):
    count = len(incident_weights)
    avg_weight = sum(incident_weights) / count if count > 0 else 0
    return count * avg_weight
```

### 7.4 KG Build Pipeline (builder.py)

**Adım 1 — Extract (Supabase'den veri çek):**
```sql
-- Incidents + category + municipality + verifications
SELECT 
  i.id, i.title, i.description, i.status,
  ST_Y(i.location::geometry) as latitude,
  ST_X(i.location::geometry) as longitude,
  i.created_at,
  i.photo_count,
  c.id as category_id, c.name as category_name,
  m.id as municipality_id, m.name as municipality_name,
  u.trust_score as reporter_trust_score,
  COUNT(v.id) FILTER (WHERE v.is_positive = true) as positive_verifications
FROM incidents i
JOIN categories c ON i.category_id = c.id
LEFT JOIN municipalities m ON ST_Contains(m.boundary, i.location)
JOIN users u ON i.reporter_id = u.id
LEFT JOIN verifications v ON v.incident_id = i.id
GROUP BY i.id, c.id, m.id, u.trust_score
```

**Adım 2 — Transform (Cluster hesaplama):**
```python
# Basit distance-threshold clustering
# Her incident için 500m içindeki diğer incidentları bul
# Aynı cluster'a ata, centroid hesapla
def build_clusters(incidents, threshold_meters=500):
    clusters = []
    assigned = set()
    for i, inc in enumerate(incidents):
        if inc.id in assigned:
            continue
        nearby = [
            other for other in incidents
            if haversine(inc.lat, inc.lng, other.lat, other.lng) <= threshold_meters
            and other.id not in assigned
        ]
        if len(nearby) >= 2:  # en az 2 incident varsa cluster oluştur
            cluster = create_cluster(nearby)
            clusters.append(cluster)
            assigned.update(n.id for n in nearby)
    return clusters
```

**Adım 3 — Load (Neo4j'e yaz):**
```cypher
-- Incident MERGE
MERGE (i:Incident {id: $id})
SET i.title = $title,
    i.status = $status,
    i.weight = $weight,
    i.latitude = $latitude,
    i.longitude = $longitude,
    i.createdAt = $createdAt

-- Relationship MERGE
MATCH (i:Incident {id: $incident_id})
MATCH (c:Category {id: $category_id})
MERGE (i)-[:BELONGS_TO]->(c)
```

**Adım 4 — Index oluştur:**
```cypher
CREATE INDEX incident_id IF NOT EXISTS FOR (i:Incident) ON (i.id);
CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name);
CREATE INDEX municipality_name IF NOT EXISTS FOR (m:Municipality) ON (m.name);
CREATE INDEX incident_status IF NOT EXISTS FOR (i:Incident) ON (i.status);
```

---

## 8. API Endpoints

### 8.1 Chat Endpoint

**`POST /chat`**

```python
# Request
class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []  # {role, content} listesi

# Response
class ChatResponse(BaseModel):
    answer: str
    related_node_ids: list[str] = []    # D3.js'te highlight edilecek node'lar
    highlight_ids: list[str] = []       # öne çıkarılacak incident id'leri
    tool_calls_made: list[str] = []     # debug için hangi tool'lar çağrıldı
```

**Auth:** JWT Bearer token zorunlu (tüm roller)

**İş akışı:**
1. JWT doğrula → role çıkar
2. `conversation_history` + yeni `message`'ı LangGraph agent'a ilet
3. Agent tool'larını çağırır, sonucu üretir
4. `answer`, `related_node_ids`, `highlight_ids` döndür

---

### 8.2 KG Graph Endpoint

**`GET /kg/graph`**

```python
# Response
class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: GraphMetadata

class GraphNode(BaseModel):
    id: str
    label: str
    type: str          # "Incident" | "Category" | "Municipality" | "LocationCluster"
    weight: float
    properties: dict   # type'a göre değişen ekstra özellikler

class GraphEdge(BaseModel):
    source: str        # node id
    target: str        # node id
    relationship: str  # "BELONGS_TO" | "IN_MUNICIPALITY" | "IN_CLUSTER" | "CONTAINS"

class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    last_sync: datetime
    node_counts: dict  # {"Incident": 45, "Category": 5, ...}
```

**Auth:** JWT zorunlu  
**Cache:** 60 saniye cache (graph sık değişmez)

---

### 8.3 KG Explain Endpoint

**`POST /kg/explain`**

```python
# Request
class ExplainRequest(BaseModel):
    node_id: str
    node_type: str     # "Incident" | "Category" | "Municipality" | "LocationCluster"

# Response
class ExplainResponse(BaseModel):
    explanation: str           # Agent'ın ürettiği doğal dil açıklaması
    related_nodes: list[dict]  # 1. derece komşular
    highlight_ids: list[str]   # ilgili incident id'leri
```

**Auth:** JWT zorunlu  
**İş akışı:** Agent'ın `explain_node` tool'unu direkt çağırır, konuşma geçmişi olmadan.

---

### 8.4 Risk Areas Endpoint

**`GET /kg/risk-areas`**

```python
# Response
class RiskAreasResponse(BaseModel):
    municipalities: list[MunicipalityRisk]

class MunicipalityRisk(BaseModel):
    id: str
    name: str
    weight: float
    open_incident_count: int
    top_categories: list[str]      # en fazla incident olan 3 kategori
    risk_level: str                # "low" | "medium" | "high" | "critical"
```

**Risk level hesabı (normalised weight'e göre):**
```
0.00 - 0.25 → "low"
0.25 - 0.50 → "medium"
0.50 - 0.75 → "high"
0.75 - 1.00 → "critical"
```

**Auth:** JWT zorunlu

---

### 8.5 KG Sync Endpoint

**`POST /kg/sync`**

```python
# Response
class SyncResponse(BaseModel):
    success: bool
    nodes_created: int
    nodes_updated: int
    relationships_created: int
    duration_seconds: float
    message: str
```

**Auth:** JWT zorunlu + **sadece Admin rolü**  
**İş akışı:** Komple KG rebuild (Neo4j'i temizle, baştan yaz).

---

## 9. LangGraph Agent — Detaylı Tasarım

### 9.1 Agent State

```python
from langgraph.graph import StateGraph, MessagesState

class AgentState(MessagesState):
    # MessagesState zaten messages listesini tutar
    # Ekstra state alanları:
    highlighted_nodes: list[str]   # D3.js için toplanacak node id'ler
    tool_calls_made: list[str]     # hangi tool'lar çağrıldı
```

### 9.2 System Prompt (prompts.py)

```python
SYSTEM_PROMPT = """
You are SafeRoad Assistant, an AI agent that helps users explore road safety 
incidents in Turkey. You have access to a Knowledge Graph containing incidents, 
categories, municipalities, and location clusters.

RULES:
- Always use tools to fetch real data — never make up incident counts or names.
- When asked about locations in Turkey, map common names to municipalities 
  (e.g., "Kadıköy", "Beşiktaş" are districts of Istanbul).
- Respond in the same language the user writes in (Turkish or English).
- Keep answers concise — 2-4 sentences unless detail is requested.
- When returning incident lists, limit to 5 most relevant unless asked for more.
- Always include the node IDs of mentioned incidents in your final response 
  so the frontend can highlight them.

KNOWLEDGE GRAPH SCHEMA:
- Incident: id, title, status (Pending/InProgress/Resolved), weight, location
- Category: name (Pothole/Flooding/Accident/Roadwork/Other)
- Municipality: name, weight (risk density score)
- LocationCluster: centroid, incidentCount, weight

TOOLS AVAILABLE:
- query_graph: Run Cypher queries on Neo4j
- get_incident_detail: Get full detail of a specific incident from .NET API
- get_risk_area: Get risk summary for a municipality
- get_nearby_incidents: Find incidents near coordinates
- explain_node: Explain a graph node and its neighbors
"""
```

### 9.3 Tools (tools.py)

**Tool 1: query_graph**
```python
@tool
async def query_graph(cypher: str) -> dict:
    """
    Execute a read-only Cypher query on the SafeRoad Knowledge Graph.
    Use this for: counting incidents, filtering by category/status/municipality,
    finding relationships between nodes.
    
    Example queries:
    - MATCH (i:Incident)-[:BELONGS_TO]->(c:Category {name:'Pothole'}) RETURN i LIMIT 5
    - MATCH (m:Municipality) RETURN m.name, m.weight ORDER BY m.weight DESC
    """
    # WRITE sorgularını engelle (güvenlik)
    forbidden = ["CREATE", "DELETE", "MERGE", "SET", "DROP"]
    if any(kw in cypher.upper() for kw in forbidden):
        return {"error": "Only read queries allowed"}
    
    async with neo4j_driver.session() as session:
        result = await session.run(cypher)
        records = await result.data()
        return {"records": records, "count": len(records)}
```

**Tool 2: get_incident_detail**
```python
@tool
async def get_incident_detail(incident_id: str) -> dict:
    """
    Get full details of a specific incident including comments and 
    verification count. Use when user asks about a specific incident by ID.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DOTNET_API_URL}/incidents/{incident_id}",
            headers={"Authorization": f"Bearer {internal_token}"}
        )
        return resp.json()
```

**Tool 3: get_risk_area**
```python
@tool
async def get_risk_area(municipality_name: str) -> dict:
    """
    Get risk summary for a municipality. Returns open incident count,
    top categories, and risk level (low/medium/high/critical).
    Use when user asks about risk in a specific area or district.
    """
    cypher = """
    MATCH (i:Incident)-[:IN_MUNICIPALITY]->(m:Municipality {name: $name})
    WHERE i.status <> 'Resolved'
    MATCH (i)-[:BELONGS_TO]->(c:Category)
    RETURN m.name, m.weight, count(i) as open_count,
           collect(DISTINCT c.name) as categories
    """
    # ... execute and format
```

**Tool 4: get_nearby_incidents**
```python
@tool
async def get_nearby_incidents(
    latitude: float, 
    longitude: float, 
    radius_meters: int = 1000
) -> dict:
    """
    Find incidents near given coordinates within radius_meters.
    Use when user asks about incidents near a specific location or 
    asks 'near me' type questions.
    Max radius: 5000 meters.
    """
    # PostGIS sorgusu için .NET API'ye git
    # veya Neo4j'de koordinat filtresi uygula
    cypher = """
    MATCH (i:Incident)
    WHERE i.latitude IS NOT NULL
    WITH i,
         point.distance(
           point({latitude: i.latitude, longitude: i.longitude}),
           point({latitude: $lat, longitude: $lng})
         ) AS dist
    WHERE dist <= $radius
    RETURN i ORDER BY dist LIMIT 10
    """
```

**Tool 5: explain_node**
```python
@tool
async def explain_node(node_id: str, node_type: str) -> dict:
    """
    Get detailed information about a graph node and its first-degree neighbors.
    Use when user clicks a node in the Knowledge Graph visualizer or asks
    to explain a specific node.
    node_type must be one of: Incident, Category, Municipality, LocationCluster
    """
    cypher = f"""
    MATCH (n:{node_type} {{id: $id}})
    OPTIONAL MATCH (n)-[r]-(neighbor)
    RETURN n, collect({{rel: type(r), node: neighbor}}) as neighbors
    """
    # ... execute, format, return node + neighbors
```

### 9.4 LangGraph StateGraph (graph.py)

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

def build_agent_graph():
    tools = [query_graph, get_incident_detail, get_risk_area, 
             get_nearby_incidents, explain_node]
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    
    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if last.tool_calls:
            return "tools"
        return END
    
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    
    return graph.compile()
```

---

## 10. Authentication & Authorization

FastAPI servisi .NET API ile **aynı JWT secret'ı** kullanır. Her endpoint'e gelen `Authorization: Bearer <token>` header'ı doğrulanır.

```python
# core/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(token = Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return {
            "user_id": payload["sub"],
            "role": payload["role"]   # "Admin" | "Municipality" | "Editor" | "User"
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(user = Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
```

---

## 11. Mock Data Seed Script

KG'nin anlamlı veri içermesi için startup'ta 60 mock incident inject edilir (eğer DB boşsa).

```python
# db/seed.py
MOCK_INCIDENTS = [
    # Istanbul - Kadıköy
    {"title": "Derin çukur - Bağdat Caddesi", "category": "Pothole", 
     "lat": 40.9764, "lng": 29.0561, "municipality": "Kadıköy",
     "status": "Pending", "verifications": 8, "trust_score": 0.85},
    
    {"title": "Sel baskını - Moda sahili", "category": "Flooding",
     "lat": 40.9833, "lng": 29.0283, "municipality": "Kadıköy",
     "status": "InProgress", "verifications": 12, "trust_score": 0.90},
    
    # Istanbul - Beşiktaş
    {"title": "Yol çalışması - Barbaros Bulvarı", "category": "Roadwork",
     "lat": 41.0430, "lng": 29.0058, "municipality": "Beşiktaş",
     "status": "InProgress", "verifications": 5, "trust_score": 0.75},
    
    # ... (toplam 60 incident, 5 ilçe, 5 kategori)
]

async def seed_if_empty(pool):
    count = await pool.fetchval("SELECT COUNT(*) FROM incidents")
    if count == 0:
        await insert_mock_incidents(pool, MOCK_INCIDENTS)
        print(f"Seeded {len(MOCK_INCIDENTS)} mock incidents")
```

---

## 12. CORS & Middleware Yapılandırması

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SafeRoad AI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],   # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 13. Implementasyon Sırası (Önerilen)

### Faz 1 — Temel Altyapı
- [ ] Proje klasör yapısını oluştur
- [ ] `requirements.txt` hazırla
- [ ] `.env` dosyasını ayarla
- [ ] `core/config.py` — Pydantic BaseSettings
- [ ] `db/supabase_client.py` — asyncpg pool
- [ ] `db/neo4j_client.py` — driver singleton
- [ ] `main.py` — FastAPI app + lifespan

### Faz 2 — Knowledge Graph
- [ ] `kg/weights.py` — formüller
- [ ] `kg/builder.py` — Extract → Transform → Load pipeline
- [ ] `kg/queries.py` — hazır Cypher sorguları
- [ ] `routers/kg.py` — `/kg/graph`, `/kg/risk-areas`
- [ ] `routers/admin.py` — `/kg/sync`
- [ ] Mock data seed script

### Faz 3 — Agent
- [ ] `agent/tools.py` — 5 tool
- [ ] `agent/prompts.py` — system prompt
- [ ] `agent/graph.py` — LangGraph StateGraph
- [ ] `routers/chat.py` — `/chat`
- [ ] `routers/kg.py` — `/kg/explain`

### Faz 4 — Test & Polish
- [ ] Her endpoint için `pytest` testi
- [ ] Token budget koruması (max_tokens limiti)
- [ ] Error handling — tool fail durumları
- [ ] Logging — her agent step'i logla

---

## 14. requirements.txt

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
pydantic-settings==2.3.0
python-dotenv==1.0.1

# Database
asyncpg==0.29.0
neo4j==5.20.0

# AI / LangGraph
langchain==0.2.0
langchain-openai==0.1.0
langgraph==0.1.0
openai==1.30.0

# HTTP client (tool call'lar için)
httpx==0.27.0

# Auth
PyJWT==2.8.0

# Utils
python-jose==3.3.0

# Dev / Test
pytest==8.2.0
pytest-asyncio==0.23.0
httpx==0.27.0   # TestClient için
```

---

## 15. Bilinen Kısıtlamalar & Kararlar

| Konu | Karar | Gerekçe |
|------|-------|---------|
| Neo4j persistence | In-memory, restart'ta rebuild | Free plan, demo scope — Supabase zaten kalıcı kaynak |
| Multi-agent (Crew) | Kullanılmıyor | $5 OpenAI bütçesi, single agent yeterli |
| GraphRAG / embeddings | Faz 4 sonrası | Şu an Cypher sorgular yeterli |
| GNN | Kullanılmıyor | Mock data ile anlamlı training yapılamaz |
| WebSocket | Yok | HTTP polling yeterli, SignalR .NET'te mevcut |
| Rate limiting | Agent başına max 5 tool call | Token koruması |

---

*SafeRoad FastAPI & KG PRD — v1.0 — Mart 2026*
