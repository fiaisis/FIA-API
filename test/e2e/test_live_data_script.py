"""
e2e for live data script fetching/editing
"""

from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

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
