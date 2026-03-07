"""
Neo4j async driver singleton.
Uses bolt protocol to connect to a local Neo4j Community instance.
"""

import logging

from neo4j import AsyncGraphDatabase, AsyncDriver

from core.config import settings

logger = logging.getLogger(__name__)

# Module-level driver reference
_driver: AsyncDriver | None = None


async def create_driver() -> AsyncDriver:
    """Create and verify the Neo4j async driver."""
    global _driver
    if _driver is not None:
        return _driver

    logger.info("Connecting to Neo4j at %s…", settings.neo4j_uri)
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    # Verify connectivity
    await _driver.verify_connectivity()
    logger.info("Neo4j connection verified")
    return _driver


async def get_driver() -> AsyncDriver:
    """Return the existing driver or create one."""
    if _driver is None:
        return await create_driver()
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")
