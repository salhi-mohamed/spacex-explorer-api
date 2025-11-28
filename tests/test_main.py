# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
# Si ton fichier FastAPI est dans app/main.py, garde l'import ci-dessous.
# Si ton main.py est à la racine, remplace par: from main import app
from app.main import app

client = TestClient(app)

def test_info_endpoint_includes_trace():
    headers = {"X-Trace-Id": "test-trace-123"}
    r = client.get("/info", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "SpaceX Explorer API" in data.get("status", "")
    assert data.get("trace_id") == "test-trace-123"

def make_mock_response(status_code=200, json_data=None):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json = Mock(return_value=json_data)
    return mock_resp

@patch("app.main.requests.get")
def test_latest_launch_endpoint(mock_get):
    sample_launch = {
        "name": "Starlink-TEST",
        "flight_number": 999,
        "date_utc": "2025-01-01T00:00:00.000Z",
        "rocket": "rocket_id_123",
        "success": True,
        "upcoming": False,
        "details": "Test flight",
        "links": {"webcast": "http://example.com", "patch": {"small": None, "large": None}}
    }
    mock_get.return_value = make_mock_response(json_data=sample_launch)
    r = client.get("/launches/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Starlink-TEST"
    assert data["flight_number"] == 999

@patch("app.main.requests.get")
def test_rockets_endpoint(mock_get):
    sample_rockets = [
        {"name": "Falcon", "type":"orbital", "first_flight":"2010-06-04", "country":"USA",
         "stages":2,"boosters":0,"cost_per_launch":50000000,"success_rate_pct":98,
         "height":{"meters":70},"diameter":{"meters":3.7},"mass":{"kg":549054},"description":"desc"}
    ]
    mock_get.return_value = make_mock_response(json_data=sample_rockets)
    r = client.get("/rockets")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Falcon"
