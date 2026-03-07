"""
Shared test fixtures for SafeRoad FastAPI tests.
"""

import os
import jwt
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

# Set environment variables BEFORE importing anything from the app
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("DOTNET_API_URL", "http://localhost:9001/api")
os.environ.setdefault("JWT_SECRET", "SafeRoadDev2026SuperSecretKeyAtLeast32Chars!!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ISSUER", "SafeRoad")
os.environ.setdefault("JWT_AUDIENCE", "SafeRoad")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from core.auth import CLAIM_NAME_IDENTIFIER, CLAIM_EMAIL, CLAIM_NAME, CLAIM_ROLE


# ── JWT Token Generation ─────────────────────────────────────

TEST_JWT_SECRET = "SafeRoadDev2026SuperSecretKeyAtLeast32Chars!!"
TEST_JWT_ALGORITHM = "HS256"


def generate_test_token(
    user_id: str = "a1a1a1a1-0000-0000-0000-000000000003",
    email: str = "john.doe@gmail.com",
    name: str = "John Doe",
    role: str = "User",
    expired: bool = False,
) -> str:
    """Generate a JWT token matching .NET backend format."""
    now = datetime.now(timezone.utc)
    payload = {
        CLAIM_NAME_IDENTIFIER: user_id,
        CLAIM_EMAIL: email,
        CLAIM_NAME: name,
        CLAIM_ROLE: role,
        "iss": "SafeRoad",
        "aud": "SafeRoad",
        "exp": now + (timedelta(hours=-1) if expired else timedelta(hours=1)),
        "iat": now,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)


@pytest.fixture
def user_token() -> str:
    return generate_test_token(role="User")


@pytest.fixture
def admin_token() -> str:
    return generate_test_token(
        user_id="a1a1a1a1-0000-0000-0000-000000000001",
        email="admin@saferoad.com",
        name="System Admin",
        role="Admin",
    )


@pytest.fixture
def expired_token() -> str:
    return generate_test_token(expired=True)


# ── Mock Neo4j Driver ────────────────────────────────────────

@pytest.fixture
def mock_neo4j_session():
    """Create a mock Neo4j async session."""
    session = AsyncMock()
    result = AsyncMock()
    result.data = AsyncMock(return_value=[])
    session.run = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def mock_neo4j_driver(mock_neo4j_session):
    """Create a mock Neo4j async driver."""
    driver = AsyncMock()
    driver.session = MagicMock(return_value=mock_neo4j_session)
    return driver


# ── Mock asyncpg Pool ────────────────────────────────────────

@pytest.fixture
def mock_pg_pool():
    """Create a mock asyncpg connection pool."""
    pool = AsyncMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchval = AsyncMock(return_value=0)
    pool.fetchrow = AsyncMock(return_value=None)
    return pool
