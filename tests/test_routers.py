"""
Integration tests for KG router endpoints.
Uses FastAPI TestClient with mocked Neo4j driver.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient

from tests.conftest import generate_test_token


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    # Patch settings before importing app
    with patch("core.config.settings") as mock_settings:
        mock_settings.jwt_secret = "SafeRoadDev2026SuperSecretKeyAtLeast32Chars!!"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = "SafeRoad"
        mock_settings.jwt_audience = "SafeRoad"
        mock_settings.neo4j_uri = "bolt://localhost:7687"
        mock_settings.neo4j_user = "neo4j"
        mock_settings.neo4j_password = "test"
        mock_settings.supabase_db_url = "postgresql://test:test@localhost/test"
        mock_settings.openai_api_key = "sk-test"
        mock_settings.dotnet_api_url = "http://localhost:9001/api"
        mock_settings.debug = True
        mock_settings.log_level = "WARNING"

        from main import app
        yield TestClient(app, raise_server_exceptions=False)


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "SafeRoad AI Service"


class TestKGGraphEndpoint:
    def test_requires_auth(self, client):
        """GET /kg/graph without token should return 401."""
        resp = client.get("/kg/graph")
        assert resp.status_code == 401

    @patch("routers.kg.get_driver")
    def test_returns_graph(self, mock_get_driver, client):
        """GET /kg/graph with valid token should return graph data."""
        # Mock Neo4j response
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[])
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_driver = AsyncMock()
        mock_driver.session = MagicMock(return_value=mock_session)
        mock_get_driver.return_value = mock_driver

        token = generate_test_token()
        resp = client.get(
            "/kg/graph",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data


class TestRiskAreasEndpoint:
    def test_requires_auth(self, client):
        resp = client.get("/kg/risk-areas")
        assert resp.status_code == 401

    @patch("routers.kg.get_driver")
    def test_returns_risk_areas(self, mock_get_driver, client):
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[
            {
                "id": "1",
                "name": "Kepez Municipality",
                "weight": 5.0,
                "incident_count": 3,
                "top_categories": ["Pothole", "Flooding"],
            }
        ])
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_driver = AsyncMock()
        mock_driver.session = MagicMock(return_value=mock_session)
        mock_get_driver.return_value = mock_driver

        token = generate_test_token()
        resp = client.get(
            "/kg/risk-areas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "municipalities" in data


class TestSyncEndpoint:
    def test_requires_admin(self, client):
        """POST /kg/sync with User role should return 403."""
        token = generate_test_token(role="User")
        resp = client.post(
            "/kg/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_no_auth(self, client):
        """POST /kg/sync without token should return 401."""
        resp = client.post("/kg/sync")
        assert resp.status_code == 401
