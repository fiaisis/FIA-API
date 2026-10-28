"""Runner discovery route tests with external services mocked."""

from http import HTTPStatus
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

from fia_api.core.auth import AUTH_URL
from fia_api.fia_api import app

RUNNER_ENDPOINTS = {
    "/jobs/runners": ("fiaisis", "mantid"),
    "/jobs/runners/mantidimaging": ("fiaisis", "mantidimaging"),
}
API_KEY_HEADER = {"Authorization": "Bearer test-api-key"}


def _jwt_headers(payload):
    token = jwt.encode(payload, "test-signing-key-with-at-least-32-bytes", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _setup():
    """Override the e2e database setup because runner discovery does not use the database."""


@pytest.fixture(params=list(RUNNER_ENDPOINTS))
def runner_endpoint(request):
    return request.param


@pytest.fixture
def github_get():
    with patch("fia_api.core.utility.requests.get") as mock_get:
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = [
            {"name": "sha256:aaa", "metadata": {"container": {"tags": ["1.0.0", "latest"]}}},
            {"name": "sha256:bbb", "metadata": {"container": {"tags": []}}},
        ]
        yield mock_get


@pytest.fixture
def auth_post():
    with patch("fia_api.core.auth.tokens.requests.post") as mock_post:
        mock_post.return_value.status_code = HTTPStatus.OK
        yield mock_post


@pytest.fixture
def client(monkeypatch, github_get, auth_post):
    monkeypatch.setenv("FIA_API_API_KEY", "test-api-key")
    monkeypatch.setattr("fia_api.core.auth.tokens.DEV_MODE", False)
    monkeypatch.setattr("fia_api.core.utility.GITHUB_PACKAGE_TOKEN", "test-package-token")
    with (
        patch("fia_api.core.utility.cache_get_json", return_value=None),
        patch("fia_api.core.utility.cache_set_json"),
        TestClient(app) as test_client,
    ):
        yield test_client


@pytest.mark.parametrize("authentication", ["jwt", "api_key"])
def test_get_runners_authenticated(client, runner_endpoint, github_get, auth_post, authentication):
    headers = _jwt_headers({"usernumber": 1234, "role": "user"}) if authentication == "jwt" else API_KEY_HEADER

    response = client.get(runner_endpoint, headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"sha256:aaa": "1.0.0"}
    org, image_name = RUNNER_ENDPOINTS[runner_endpoint]
    github_get.assert_called_once_with(
        f"https://api.github.com/orgs/{org}/packages/container/{image_name}/versions",
        headers={"Authorization": "Bearer test-package-token"},
        timeout=10,
    )
    if authentication == "jwt":
        auth_post.assert_called_once_with(
            f"{AUTH_URL}/verify", json={"token": headers["Authorization"].removeprefix("Bearer ")}, timeout=30
        )
    else:
        auth_post.assert_not_called()


def test_get_runners_empty(client, runner_endpoint, github_get):
    github_get.return_value.json.return_value = []

    response = client.get(runner_endpoint, headers=API_KEY_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "foo"}])
def test_get_runners_missing_bearer_credentials(client, runner_endpoint, github_get, auth_post, headers):
    response = client.get(runner_endpoint, headers=headers)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    github_get.assert_not_called()
    auth_post.assert_not_called()


def test_get_runners_invalid_token(client, runner_endpoint, github_get, auth_post):
    auth_post.return_value.status_code = HTTPStatus.FORBIDDEN

    response = client.get(runner_endpoint, headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    github_get.assert_not_called()


@pytest.mark.parametrize("missing_field", ["role", "usernumber"])
def test_get_runners_missing_user_details(client, runner_endpoint, github_get, missing_field):
    payload = {"usernumber": 1234, "role": "user"}
    del payload[missing_field]

    response = client.get(runner_endpoint, headers=_jwt_headers(payload))

    assert response.status_code == HTTPStatus.FORBIDDEN
    github_get.assert_not_called()


@pytest.mark.parametrize(
    "github_status", [HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]
)
def test_get_runners_github_failure(client, runner_endpoint, github_get, github_status):
    github_get.return_value.status_code = github_status

    response = client.get(runner_endpoint, headers=API_KEY_HEADER)

    assert response.status_code == HTTPStatus.FAILED_DEPENDENCY
    assert response.json() == "Github API request failed "
