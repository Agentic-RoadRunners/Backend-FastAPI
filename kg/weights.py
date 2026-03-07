"""
Node weight calculation formulas for the Knowledge Graph.

These weights determine the visual size / importance of nodes in the D3.js frontend.
TrustScore from the DB is an integer (default 100) — normalized to 0-1 by dividing by 100.
IncidentStatus uses real DB values: Pending, Verified, Disputed, Resolved.
"""


def incident_weight(
    positive_verifications: int,
    reporter_trust_score: int,
    status: str,
    photo_count: int,
) -> float:
    """
    Calculate the weight of an Incident node.

    Formula:
        base = (positive_verifications * 0.4) + (trust_normalized * 0.6)
        bonus = 0.1 per photo (max 0.3)
        weight = base * status_multiplier + bonus

    Args:
        positive_verifications: Number of positive verifications.
        reporter_trust_score: Integer trust score (0-100+) from DB.
        status: One of "Pending", "Verified", "Disputed", "Resolved".
        photo_count: Number of photos attached to the incident.

    Returns:
        Calculated weight as a float.
    """
    status_multiplier = {
        "Pending": 1.5,
        "Verified": 1.2,
        "Disputed": 0.8,
        "Resolved": 0.3,
    }

    trust_normalized = min(reporter_trust_score / 100.0, 1.0)
    base = (positive_verifications * 0.4) + (trust_normalized * 0.6)
    bonus = min(photo_count * 0.1, 0.3)

    return base * status_multiplier.get(status, 1.0) + bonus


def category_weight(open_incident_count: int) -> float:
    """
    Category weight = number of open (non-Resolved) incidents in this category.
    """
    return float(open_incident_count)


def municipality_weight(
    incident_weights_sum: float,
    boundary_area_km2: float,
) -> float:
    """
    Municipality weight = density of weighted incidents per km².
    Falls back to raw sum if area is zero or unknown.
    """
    if boundary_area_km2 <= 0:
        return incident_weights_sum
    return incident_weights_sum / boundary_area_km2


def cluster_weight(incident_weights: list[float]) -> float:
    """
    LocationCluster weight = count * average_weight.
    Rewards both density and severity.
    """
    count = len(incident_weights)
    if count == 0:
        return 0.0
    avg_weight = sum(incident_weights) / count
    return count * avg_weight
