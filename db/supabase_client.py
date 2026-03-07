"""
Supabase PostgreSQL connection pool using asyncpg.

IMPORTANT: The .NET backend uses PascalCase column names with quoted identifiers.
All SQL queries must use "ColumnName" syntax (double-quoted).
"""

import logging

import asyncpg

from core.config import settings

logger = logging.getLogger(__name__)

# Module-level pool reference
_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    """Create and return the asyncpg connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    logger.info("Creating asyncpg connection pool to Supabase…")
    _pool = await asyncpg.create_pool(
        dsn=settings.supabase_db_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    logger.info("asyncpg pool created successfully")
    return _pool


async def get_pool() -> asyncpg.Pool:
    """Return the existing pool or create one."""
    if _pool is None:
        return await create_pool()
    return _pool


async def close_pool() -> None:
    """Close the asyncpg connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("asyncpg pool closed")
