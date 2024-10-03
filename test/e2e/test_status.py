from starlette.testclient import TestClient

from fia_api.fia_api import app

client = TestClient(app)


def test_put_instrument_status_returns_true():
    """Test instrument status returns true when set to true."""
    client.put("/instrument/mari/status?status=true", headers={"Authorization": "Bearer shh"})
    get_response = client.get("/instrument/mari/specification", headers={"Authorization": "Bearer shh"})
    assert get_response.json()["enabled"] is True
