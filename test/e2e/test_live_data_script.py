"""
e2e for live data script fetching/editing
"""

import json
from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.core.cache import get_valkey_client
from fia_api.fia_api import app
from fia_api.routers.live_data import _get_traceback_key

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


@patch("fia_api.core.auth.tokens.requests.post")
def test_live_data_traceback_fetching_and_clearing(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK

    # Simulate a traceback being set in the cache
    traceback_content = "Exception: Some error occurred during live data processing"
    client_cache = get_valkey_client()
    client_cache.set(_get_traceback_key("test"), traceback_content, ex=60)

    # Verify the traceback can be fetched
    response = client.get("/live-data/test/traceback", headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == traceback_content

    # Update the script, which should clear the cache
    client.put("/live-data/test/script", json={"value": "print('fixed error')"}, headers=API_KEY_HEADER)

    # Verify the traceback is now cleared
    response = client.get("/live-data/test/traceback", headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == "null"

    # Revert for safety
    client.put("/live-data/test/script", json={"value": "Reverted"}, headers=API_KEY_HEADER)


@patch("fia_api.core.auth.tokens.requests.post")
def test_stream_logs_success(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    client_cache = get_valkey_client()
    stream_key = "test_live_data_processor_logs"
    client_cache.delete(stream_key)  # Ensure clean slate
    client_cache.xadd(stream_key, {"msg": "test_log_1"})
    client_cache.xadd(stream_key, {"msg": "test_log_2"})

    with client.stream("GET", "/live-data/test/logs", headers=API_KEY_HEADER) as response:
        assert response.status_code == HTTPStatus.OK

        # Read two events from the SSE stream
        lines = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                lines.append(line)
            if len(lines) == 2:
                break

        assert len(lines) == 2
        data1 = json.loads(lines[0][6:])
        data2 = json.loads(lines[1][6:])
        assert data1["msg"] == "test_log_1"
        assert data2["msg"] == "test_log_2"


def test_stream_logs_unauthorized():
    response = client.get("/live-data/test/logs")
    assert response.status_code == HTTPStatus.FORBIDDEN
