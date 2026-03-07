"""
Tests for KG builder pipeline (kg/builder.py).
"""

import pytest
from kg.builder import (
    _haversine,
    _build_clusters,
    _compute_incident_weights,
    _compute_category_weights,
    _compute_municipality_weights,
    _assign_clusters_to_municipalities,
    CLUSTER_THRESHOLD_METERS,
)


class TestHaversine:
    def test_same_point(self):
        assert _haversine(36.89, 30.71, 36.89, 30.71) == 0.0

    def test_known_distance(self):
        # Antalya center to Kepez (~5km roughly)
        dist = _haversine(36.8969, 30.7133, 36.93, 30.73)
        assert 3_000 < dist < 7_000  # within reasonable range

    def test_symmetric(self):
        d1 = _haversine(36.89, 30.71, 36.90, 30.72)
        d2 = _haversine(36.90, 30.72, 36.89, 30.71)
        assert abs(d1 - d2) < 0.01


class TestBuildClusters:
    def test_single_cluster(self):
        """Two nearby incidents should be in the same cluster."""
        incidents = [
            {"id": "1", "latitude": 36.89, "longitude": 30.71, "weight": 1.0},
            {"id": "2", "latitude": 36.8905, "longitude": 30.7105, "weight": 2.0},
        ]
        clusters = _build_clusters(incidents)
        assert len(clusters) == 1
        assert len(clusters[0]["incident_ids"]) == 2

    def test_separate_clusters(self):
        """Two far-apart incidents should be in different clusters."""
        incidents = [
            {"id": "1", "latitude": 36.89, "longitude": 30.71, "weight": 1.0},
            {"id": "2", "latitude": 37.0, "longitude": 31.0, "weight": 2.0},
        ]
        clusters = _build_clusters(incidents)
        assert len(clusters) == 2

    def test_empty_input(self):
        assert _build_clusters([]) == []

    def test_missing_coordinates(self):
        """Incidents without lat/lon should be skipped."""
        incidents = [{"id": "1", "latitude": None, "longitude": None, "weight": 1.0}]
        clusters = _build_clusters(incidents)
        assert len(clusters) == 0


class TestComputeWeights:
    def test_incident_weights_attached(self):
        incidents = [
            {
                "id": "1",
                "positive_verifications": 2,
                "reporter_trust_score": 100,
                "status": "Pending",
                "photo_count": 1,
            }
        ]
        result = _compute_incident_weights(incidents)
        assert "weight" in result[0]
        assert result[0]["weight"] > 0

    def test_category_weights(self):
        categories = [{"id": 1, "name": "Pothole"}, {"id": 2, "name": "Flooding"}]
        incidents = [
            {"category_id": 1, "status": "Pending"},
            {"category_id": 1, "status": "Verified"},
            {"category_id": 2, "status": "Resolved"},
        ]
        result = _compute_category_weights(categories, incidents)
        # Category 1: 2 open incidents, Category 2: 0 open
        assert result[0]["weight"] == 2.0
        assert result[1]["weight"] == 0.0

    def test_municipality_weights(self):
        municipalities = [{"id": 1, "name": "Antalya", "area_km2": 10.0}]
        incidents = [
            {"municipality_id": 1, "weight": 5.0},
            {"municipality_id": 1, "weight": 3.0},
        ]
        result = _compute_municipality_weights(municipalities, incidents)
        # sum=8.0, area=10.0 → weight=0.8
        assert abs(result[0]["weight"] - 0.8) < 0.01


class TestAssignClusters:
    def test_majority_municipality(self):
        clusters = [
            {"id": "c1", "incident_ids": ["1", "2", "3"]}
        ]
        incidents = [
            {"id": "1", "municipality_id": 1},
            {"id": "2", "municipality_id": 1},
            {"id": "3", "municipality_id": 2},
        ]
        result = _assign_clusters_to_municipalities(clusters, incidents)
        assert result[0]["municipality_id"] == 1

    def test_no_municipality(self):
        clusters = [{"id": "c1", "incident_ids": ["1"]}]
        incidents = [{"id": "1", "municipality_id": None}]
        result = _assign_clusters_to_municipalities(clusters, incidents)
        assert result[0]["municipality_id"] is None
