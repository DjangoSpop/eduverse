"""
Tests for health and root endpoints.
"""

import pytest


def test_root_endpoint(client):
    """Test root endpoint returns correct structure"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "operational"
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "storage" in data


def test_stats_endpoint(client):
    """Test stats endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200

    data = response.json()
    assert "storage" in data
    assert "endpoints" in data

    storage = data["storage"]
    assert "curriculum_count" in storage
    assert "lesson_count" in storage
    assert "learner_count" in storage
    assert "session_count" in storage
    assert storage["total_entities"] == 0  # Should be empty at start
