"""
Tests for KG weight calculation formulas (kg/weights.py).
"""

import pytest
from kg.weights import (
    incident_weight,
    category_weight,
    municipality_weight,
    cluster_weight,
)


class TestIncidentWeight:
    """Test incident_weight formula."""

    def test_pending_high_trust(self):
        """Pending incident with high trust and verifications should have high weight."""
        w = incident_weight(
            positive_verifications=5,
            reporter_trust_score=100,
            status="Pending",
            photo_count=2,
        )
        # base = (5*0.4) + (1.0*0.6) = 2.6
        # bonus = min(2*0.1, 0.3) = 0.2
        # weight = 2.6 * 1.5 + 0.2 = 4.1
        assert abs(w - 4.1) < 0.01

    def test_resolved_low_weight(self):
        """Resolved incident should have low weight."""
        w = incident_weight(
            positive_verifications=0,
            reporter_trust_score=50,
            status="Resolved",
            photo_count=0,
        )
        # base = (0*0.4) + (0.5*0.6) = 0.3
        # bonus = 0
        # weight = 0.3 * 0.3 = 0.09
        assert abs(w - 0.09) < 0.01

    def test_verified_status(self):
        """Verified status should have 1.2 multiplier."""
        w = incident_weight(
            positive_verifications=2,
            reporter_trust_score=80,
            status="Verified",
            photo_count=1,
        )
        # base = (2*0.4) + (0.8*0.6) = 1.28
        # bonus = 0.1
        # weight = 1.28 * 1.2 + 0.1 = 1.636
        assert abs(w - 1.636) < 0.01

    def test_disputed_status(self):
        """Disputed status should have 0.8 multiplier."""
        w = incident_weight(
            positive_verifications=1,
            reporter_trust_score=100,
            status="Disputed",
            photo_count=0,
        )
        # base = (1*0.4) + (1.0*0.6) = 1.0
        # weight = 1.0 * 0.8 = 0.8
        assert abs(w - 0.8) < 0.01

    def test_photo_bonus_capped(self):
        """Photo bonus should cap at 0.3."""
        w1 = incident_weight(0, 100, "Pending", photo_count=3)
        w2 = incident_weight(0, 100, "Pending", photo_count=10)
        # Both should have the same bonus (0.3)
        assert abs(w1 - w2) < 0.01

    def test_trust_score_normalization(self):
        """Trust score above 100 should be capped at 1.0."""
        w = incident_weight(0, 200, "Pending", 0)
        # trust_normalized = min(200/100, 1.0) = 1.0
        # base = 0 + 1.0*0.6 = 0.6
        # weight = 0.6 * 1.5 = 0.9
        assert abs(w - 0.9) < 0.01


class TestCategoryWeight:
    def test_basic(self):
        assert category_weight(10) == 10.0

    def test_zero(self):
        assert category_weight(0) == 0.0


class TestMunicipalityWeight:
    def test_density(self):
        w = municipality_weight(10.0, 2.0)
        assert abs(w - 5.0) < 0.01

    def test_zero_area_fallback(self):
        """Zero area should return raw weight sum."""
        w = municipality_weight(10.0, 0)
        assert abs(w - 10.0) < 0.01


class TestClusterWeight:
    def test_basic(self):
        w = cluster_weight([1.0, 2.0, 3.0])
        # count=3, avg=2.0, weight=6.0
        assert abs(w - 6.0) < 0.01

    def test_empty(self):
        assert cluster_weight([]) == 0.0

    def test_single(self):
        w = cluster_weight([5.0])
        assert abs(w - 5.0) < 0.01
