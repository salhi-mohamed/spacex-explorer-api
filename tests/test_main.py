import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
import logging

# ------------------ Setup logging ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_logger")

client = TestClient(app)

# ------------------ Helper ------------------
def make_mock_response(status_code=200, json_data=None):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json = Mock(return_value=json_data)
    return mock_resp

# ------------------ /info ------------------
def test_info_endpoint_includes_trace():
    headers = {"X-Trace-Id": "trace-123"}
    r = client.get("/info", headers=headers)
    logger.info(f"Testing /info endpoint, status: {r.status_code}, response: {r.json()}")
    assert r.status_code == 200
    data = r.json()
    assert "SpaceX Explorer API" in data.get("status", "")
    assert data.get("trace_id") == "trace-123"

# ------------------ Dynamic endpoint tests ------------------
endpoint_tests = [
    {
        "path": "/launches/latest",
        "sample": {
            "name": "Starlink-TEST",
            "flight_number": 999
        }
    },
    {
        "path": "/launches/123",
        "sample": {
            "name": "Test-Launch-123",
            "flight_number": 123
        }
    },
    {
        "path": "/rockets",
        "sample": [
            {"name": "Falcon", "cost_per_launch": 50000000}
        ]
    },
    {
        "path": "/rockets/rocket_id_123",
        "sample": {
            "name": "Falcon-Heavy",
            "cost_per_launch": 90000000
        }
    },
]

# ------------------ Parametrized test with endpoint names ------------------
@pytest.mark.parametrize("endpoint", endpoint_tests, ids=[e["path"] for e in endpoint_tests])
@patch("app.main.requests.get")
def test_endpoints(mock_get, endpoint):
    mock_get.return_value = make_mock_response(json_data=endpoint["sample"])
    r = client.get(endpoint["path"])
    logger.info(f"Testing {endpoint['path']}, status: {r.status_code}, response: {r.json()}")
    assert r.status_code == 200
    data = r.json()
    if isinstance(endpoint["sample"], list):
        assert isinstance(data, list)
        assert data[0]["name"] == endpoint["sample"][0]["name"]
    else:
        assert isinstance(data, dict)
        assert data["name"] == endpoint["sample"]["name"]
