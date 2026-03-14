"""
Neo4j SYNCHRONOUS driver singleton.

Kullanım amacı: CrewAI araçları (crew_tools.py) thread pool executor içinde
(run_in_executor) çalışır — event loop yoktur. Bu yüzden async driver yerine
sync GraphDatabase.driver kullanmak gerekir.

UYARI: Bu modülü async koddan ASLA doğrudan kullanmayın.
       Async kod için db.neo4j_client modülünü (AsyncGraphDatabase) kullanın.
"""

import logging
import threading

from neo4j import GraphDatabase, Driver

from core.config import settings

logger = logging.getLogger(__name__)

_sync_driver: Driver | None = None
_lock = threading.Lock()  # Thread-safe lazy init için


def get_sync_driver() -> Driver:
    """
    Sync Neo4j driver'ını döndürür; yoksa oluşturur.
    Thread-safe — birden fazla thread aynı anda çağırabilir.
    """
    global _sync_driver
    if _sync_driver is None:
        with _lock:
            if _sync_driver is None:  # double-checked locking
                logger.info("Sync Neo4j driver oluşturuluyor: %s", settings.neo4j_uri)
                _sync_driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                )
                _sync_driver.verify_connectivity()
                logger.info("Sync Neo4j driver hazır")
    return _sync_driver


def close_sync_driver() -> None:
    """Sync driver'ı kapat. Uygulama shutdown'ında lifespan tarafından çağrılır."""
    global _sync_driver
    with _lock:
        if _sync_driver is not None:
            _sync_driver.close()
            _sync_driver = None
            logger.info("Sync Neo4j driver kapatıldı")
