import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import sys

# Add the server directory to sys.path to allow importing main and escalation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from main import app

client = TestClient(app)

# Set up a mock API secret for testing
os.environ["API_SECRET"] = "test_secret"

def test_escalation_endpoint_success():
    """Test successful escalation request."""
    mock_payload = {
        "content": "Alert! Something is wrong.",
        "author": "Tester",
        "author_id": "123",
        "channel": "general",
        "channel_id": "456",
        "guild": "Test Server",
        "guild_id": "789",
        "timestamp": "2023-10-27T10:00:00+00:00"
    }
    
    with patch("main.escalation_function") as mock_escalation:
        mock_escalation.return_value = "Mocked Result"
        
        response = client.post(
            "/api/v1/bot",
            json=mock_payload,
            headers={"x-secret": "test_secret"}
        )
        
        assert response.status_code == 200
        mock_escalation.assert_called_once()

def test_escalation_endpoint_unauthorized():
    """Test request with invalid or missing secret."""
    mock_payload = {
        "content": "Test content",
        "author": "Tester",
        "author_id": "123",
        "channel": "general",
        "channel_id": "456",
        "guild": "Test Server",
        "guild_id": "789",
        "timestamp": "2023-10-27T10:00:00+00:00"
    }
    
    # Missing header
    response = client.post("/api/v1/bot", json=mock_payload)
    assert response.status_code == 401
    
    # Incorrect header
    response = client.post(
        "/api/v1/bot",
        json=mock_payload,
        headers={"x-secret": "wrong_secret"}
    )
    assert response.status_code == 401

def test_escalation_endpoint_invalid_data():
    """Test request with malformed data."""
    # Missing required fields
    invalid_payload = {"content": "Oops"}
    
    response = client.post(
        "/api/v1/bot",
        json=invalid_payload,
        headers={"x-secret": "test_secret"}
    )
    
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation error)
