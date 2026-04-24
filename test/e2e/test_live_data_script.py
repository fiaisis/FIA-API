"""
e2e for live data script fetching/editing
"""

import json
from http import HTTPStatus
from unittest.mock import patch, MagicMock

from starlette.testclient import TestClient

from fia_api.core.cache import get_valkey_client
from fia_api.fia_api import app

from .constants import API_KEY_HEADER, USER_HEADER

client = TestClient(app)


@patch("fia_api.core.auth.tokens.requests.post")
def test_live_data_script_updating_and_fetching(mock_post, faker):
    mock_post.return_value.status_code = HTTPStatus.OK
    script_line_1 = faker.text()
    script_line_2 = faker.text()
    expected_script = f"{script_line_1}\n{script_line_2}"
    client.put("/live-data/test/script", json={"value": expected_script}, headers=API_KEY_HEADER)
    response = client.get("/live-data/test/script", headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == expected_script
    # Revert
    client.put("/live-data/test/script", json={"value": "Reverted"}, headers=API_KEY_HEADER)


@patch("fia_api.core.auth.tokens.requests.post")
def test_live_data_script_updating_bad_creds(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.put("/live-data/test/script", json={"value": "print('hello world')"}, headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_stream_logs_unauthorized():
    response = client.get("/live-data/test/logs")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_stream_logs_success():
    """
    Test streaming logs using the real Valkey instance in CI.
    """
    valkey_client = get_valkey_client()
    instrument = "test"
    stream_key = f"{instrument}_live_data_processor_logs"

    # Clear the stream to ensure isolation between test runs
    valkey_client.delete(stream_key)

    # Seed a test log message into the stream
    test_message = {"msg": "E2E integration test log", "level": "INFO"}
    valkey_client.xadd(stream_key, test_message)

    with client.stream("GET", f"/live-data/{instrument}/logs", headers=API_KEY_HEADER) as response:
        assert response.status_code == HTTPStatus.OK

        for line in response.iter_lines():
            if line and line.startswith("data: "):
                payload = json.loads(line[6:])

                # Verify we got our seeded message
                assert payload["msg"] == test_message["msg"]
                assert payload["level"] == test_message["level"]

                break




@patch("fia_api.core.cache.get_valkey_client")
def test_stream_logs_valkey_error(mock_get_client):
    """
    Test that a Valkey exception is caught and yielded to the client safely.
    """
    mock_client = MagicMock()
    error_msg = "Simulated Valkey Connection Refused"
    mock_client.xread.side_effect = Exception(error_msg)
    mock_get_client.return_value = mock_client

    instrument = "test"

    with client.stream("GET", f"/live-data/{instrument}/logs", headers=API_KEY_HEADER) as response:
        assert response.status_code == HTTPStatus.OK

        for line in response.iter_lines():
            if line and line.startswith("data: "):
                payload = json.loads(line[6:])

                assert "error" in payload
                assert payload["error"] == error_msg

                break
