"""
POST /crew/analyze — CrewAI KG enrichment trigger.

Bu endpoint ASP.NET Core tarafından yeni bir incident oluşturulduğunda
fire-and-forget olarak çağrılır. Anında 202 Accepted döndürür ve
CrewAI crew'unu arka planda thread pool executor'da çalıştırır.

Auth yok — internal endpoint (sadece localhost:9001 tarafından çağrılır).
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel

from db.neo4j_sync_client import get_sync_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crew", tags=["Crew"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic modeller
# ─────────────────────────────────────────────────────────────────────────────

class IncidentAnalysisRequest(BaseModel):
    incident_id: str
    title: str
    description: str
    category: str
    lat: float
    lng: float
    status: str = "Pending"


class IncidentAnalysisResponse(BaseModel):
    accepted: bool
    incident_id: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=IncidentAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_incident(
    request: IncidentAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """
    Yeni incident için CrewAI KG enrichment analizini arka planda başlatır.
    Kullanıcıyı bekletmez — anında 202 döner.
    """
    background_tasks.add_task(_run_crew_analysis, request)

    return IncidentAnalysisResponse(
        accepted=True,
        incident_id=request.incident_id,
        message="KG enrichment analizi arka planda başlatıldı",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Background task
# ─────────────────────────────────────────────────────────────────────────────

def _seed_incident_node(req: IncidentAnalysisRequest) -> None:
    """
    Crew çalışmadan önce incident node'unun Neo4j'de var olduğundan emin olur.
    KG builder henüz bu incident'ı eklemediyse temel bir node oluşturur.
    Mevcut node varsa hiçbir şey değişmez (MERGE idempotent).
    """
    cypher = """
    MERGE (i:Incident {id: $id})
    ON CREATE SET
        i.title      = $title,
        i.latitude   = $lat,
        i.longitude  = $lng,
        i.status     = $status,
        i.weight     = 1.0,
        i.createdAt  = datetime()
    """
    try:
        driver = get_sync_driver()
        with driver.session() as session:
            session.run(
                cypher,
                id=req.incident_id,
                title=req.title,
                lat=req.lat,
                lng=req.lng,
                status=req.status,
            )
        logger.debug("Incident node seed tamamlandı: %s", req.incident_id)
    except Exception as e:
        logger.warning("Incident node seed başarısız (devam ediliyor): %s — %s", req.incident_id, e)


async def _run_crew_analysis(request: IncidentAnalysisRequest) -> None:
    """
    Background coroutine — CrewAI crew'unu thread pool executor'da çalıştırır.
    60 saniye timeout ile korunur.
    """
    # Lazy import — crew modülü sadece ilk background task'ta yüklenir.
    # Bu, startup süresini kısaltır ve crewai import maliyetini erteler.
    from agent.crew import crew

    logger.info("CrewAI analizi başladı: %s", request.incident_id)

    # Neo4j'de incident node'unun varlığını garantile
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _seed_incident_node, request)

    inputs = {
        "incident_id": request.incident_id,
        "title": request.title,
        "description": request.description,
        "category": request.category,
        "lat": request.lat,
        "lng": request.lng,
    }

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: crew.kickoff(inputs=inputs)),
            timeout=60.0,
        )
        logger.info(
            "CrewAI analizi tamamlandı: %s | sonuç: %s",
            request.incident_id,
            str(result)[:200],  # Log'u kısa tut
        )
    except asyncio.TimeoutError:
        logger.error(
            "CrewAI analizi zaman aşımına uğradı (60s): %s",
            request.incident_id,
        )
    except Exception as e:
        logger.error(
            "CrewAI analizi başarısız: %s — %s",
            request.incident_id,
            e,
            exc_info=True,
        )
