"""Tests for script analysis: the /script/analyse route, its service layer, and the size cap."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from http import HTTPStatus
from unittest.mock import Mock, patch

import jwt
import pytest
import requests
from redis.exceptions import RedisError
from starlette.testclient import TestClient

from fia_api.core.auth.tokens import JWTAPIBearer
from fia_api.core.request_models import AnalyseRequest
from fia_api.core.services import script_validation
from fia_api.core.services.script_validation import (
    MAX_SCRIPT_BYTES,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    SCRIPT_ANALYSE_CACHE_TTL_SECONDS,
    SCRIPT_ANALYSE_TIMEOUT_SECONDS,
    analyse_script_for_user,
    check_rate_limit,
)
from fia_api.fia_api import app

API_KEY = "script-analysis-test-api-key"

#: Mirrors the cap in mantid-python-script-lsp, which is set by the same-named environment variable.
SERVICE_MAX_SCRIPT_BYTES = 200_000

#: A four-byte character, so a script can be over the cap in bytes and under it in characters.
EMOJI = "\U0001f600"
CAP_BYTES = 8

CLEAN = {"content_hash": "hash-1", "parses": True, "diagnostics": [], "truncated": False}

BROKEN = {
    "content_hash": "hash-1",
    "parses": False,
    "diagnostics": [
        {
            "message": "undefined name 'BinMQ'",
            "severity": "warning",
            "source": "pyflakes",
            "start_line": 4,
            "start_column": 9,
            "end_line": 4,
            "end_column": 14,
        }
    ],
    "truncated": False,
}

REQUEST = AnalyseRequest(content="from mantid.simpleapi import *\n", content_hash="hash-1")


def _upstream(status: int = HTTPStatus.OK, body: object = BROKEN) -> Mock:
    response = Mock()
    response.status_code = status
    response.json.return_value = body
    return response


@contextmanager
def cap_at(limit: int) -> Iterator[None]:
    """Pin the size cap, so the boundary cases are readable rather than 200 KB of emoji."""
    with patch.object(script_validation, "MAX_SCRIPT_BYTES", limit):
        yield


@pytest.fixture
def cache_empty() -> Mock:
    """A Valkey with nothing cached, so the request actually reaches the analysis service."""
    with (
        patch("fia_api.core.services.script_validation.cache_get_json", return_value=None) as cache_get,
        patch("fia_api.core.services.script_validation.cache_set_json"),
    ):
        yield cache_get


@pytest.fixture
def valkey_off() -> None:
    """Valkey unavailable: the cache no-ops and the rate limiter must fail open."""
    with patch("fia_api.core.services.script_validation.get_valkey_client", return_value=None):
        yield


# --- size cap ---------------------------------------------------------------------------------------


def test_max_script_bytes_matches_the_analysis_service_default() -> None:
    """The cap must mean the same thing on both sides, or scripts pass one service and are refused the other.

    Both defaults are named `MAX_SCRIPT_BYTES` and set from the environment; nothing but this test keeps
    the two defaults together, so changing one without the other fails here.
    """
    assert MAX_SCRIPT_BYTES == SERVICE_MAX_SCRIPT_BYTES


def test_the_size_cap_counts_bytes_not_characters(cache_empty: Mock, valkey_off: None) -> None:
    """`len(content)` and the byte count disagree for any script with a non-ASCII character in it."""
    under_cap = EMOJI * 2  # 2 characters, 8 bytes
    over_cap = EMOJI * 3  # 3 characters, 12 bytes: over the cap by bytes, well under it by characters
    with cap_at(CAP_BYTES), analysis_service() as post:
        accepted = analyse_script_for_user(AnalyseRequest(content=under_cap, content_hash="two"), 1234)
        refused = analyse_script_for_user(AnalyseRequest(content=over_cap, content_hash="three"), 1234)

    assert accepted.status_code == HTTPStatus.OK
    assert refused.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    post.assert_called_once()  # only the script under the cap was worth forwarding
    assert refused.body["detail"] == {
        "reason": "too_large",
        "limit_bytes": CAP_BYTES,
        "actual_bytes": len(over_cap.encode("utf-8")),
    }


def test_an_ok_script_is_accepted(cache_empty: Mock, valkey_off: None) -> None:
    with patch("requests.post", return_value=_upstream()) as post:
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.OK
    assert post.call_args.args[0].endswith("/analyse")


# --- configuration ----------------------------------------------------------------------------------


def test_a_trailing_slash_on_the_service_url_does_not_double_up(cache_empty: Mock, valkey_off: None) -> None:
    """The URL is a deployment value, and `//analyse` is a different path as far as anything downstream sees."""
    with (
        patch.object(script_validation, "SCRIPT_LSP_URL", "http://mantid-python-script-lsp-service:80/"),
        patch("requests.post", return_value=_upstream()) as post,
    ):
        analyse_script_for_user(REQUEST, user_number=1234)

    assert post.call_args.args[0] == "http://mantid-python-script-lsp-service:80/analyse"


# --- rate limiting ----------------------------------------------------------------------------------


def test_check_rate_limit_fails_open_when_valkey_is_unavailable(valkey_off: None) -> None:
    for _ in range(RATE_LIMIT_MAX_REQUESTS * 3):
        assert check_rate_limit(1234) is None


def test_check_rate_limit_allows_up_to_the_limit_then_reports_the_window(valkey_off: None) -> None:
    valkey = Mock()
    valkey.incr.side_effect = list(range(1, RATE_LIMIT_MAX_REQUESTS + 2))
    with patch("fia_api.core.services.script_validation.get_valkey_client", return_value=valkey):
        for _ in range(RATE_LIMIT_MAX_REQUESTS):
            assert check_rate_limit(1234) is None

        retry_after = check_rate_limit(1234)

    assert retry_after is not None
    assert 0 < retry_after <= RATE_LIMIT_WINDOW_SECONDS


def test_check_rate_limit_expires_the_window_key_on_the_first_request(valkey_off: None) -> None:
    valkey = Mock()
    valkey.incr.return_value = 1
    with patch("fia_api.core.services.script_validation.get_valkey_client", return_value=valkey):
        check_rate_limit(1234)

    valkey.expire.assert_called_once()
    assert valkey.expire.call_args.args[1] == RATE_LIMIT_WINDOW_SECONDS
    assert valkey.expire.call_args.args[0].startswith("script_analyse_rate:v1:1234:")


def test_check_rate_limit_fails_open_when_valkey_errors(valkey_off: None) -> None:
    valkey = Mock()
    valkey.incr.side_effect = RedisError("boom")
    with patch("fia_api.core.services.script_validation.get_valkey_client", return_value=valkey):
        assert check_rate_limit(1234) is None


def test_a_rate_limited_request_does_not_reach_the_analysis_service(cache_empty: Mock, valkey_off: None) -> None:
    over_limit = Mock()
    over_limit.incr.return_value = RATE_LIMIT_MAX_REQUESTS + 1
    with (
        patch("fia_api.core.services.script_validation.get_valkey_client", return_value=over_limit),
        patch("requests.post") as post,
    ):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert result.body["detail"]["reason"] == "rate_limited"
    assert result.retry_after_seconds is not None
    post.assert_not_called()


# --- forwarding to mantid-python-script-lsp ---------------------------------------------------------


def test_the_upstream_status_and_body_are_forwarded_unchanged(cache_empty: Mock, valkey_off: None) -> None:
    with patch("requests.post", return_value=_upstream()) as post:
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.OK
    assert result.body == BROKEN
    post.assert_called_once_with(
        f"{script_validation.SCRIPT_LSP_URL}/analyse",
        json={"content": REQUEST.content, "content_hash": "hash-1"},
        timeout=SCRIPT_ANALYSE_TIMEOUT_SECONDS,
    )


@pytest.mark.parametrize(
    ("upstream_status", "upstream_body"),
    [
        (HTTPStatus.SERVICE_UNAVAILABLE, {"detail": {"reason": "warming_up", "detail": "Mantid is loading"}}),
        (HTTPStatus.TOO_MANY_REQUESTS, {"detail": {"reason": "busy", "retry_after_seconds": 1}}),
        (HTTPStatus.GATEWAY_TIMEOUT, {"detail": {"reason": "timed_out"}}),
    ],
)
def test_upstream_failure_statuses_are_passed_through(
    cache_empty: Mock,
    valkey_off: None,
    upstream_status: int,
    upstream_body: dict[str, object],
) -> None:
    """503 must not be flattened into 500: the frontend shows "still warming up" only because of it."""
    upstream = _upstream(status=upstream_status, body=upstream_body)
    with patch("requests.post", return_value=upstream):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == upstream_status
    assert result.body == upstream_body


def test_an_ok_result_is_cached_under_the_content_hash(valkey_off: None) -> None:
    with (
        patch("fia_api.core.services.script_validation.cache_get_json", return_value=None),
        patch("fia_api.core.services.script_validation.cache_set_json") as cache_set,
        patch("requests.post", return_value=_upstream()),
    ):
        analyse_script_for_user(REQUEST, user_number=1234)

    key = cache_set.call_args.args[0]
    assert key.startswith("script_analyse:v1:")
    assert cache_set.call_args.args[1] == BROKEN
    assert cache_set.call_args.args[2] == SCRIPT_ANALYSE_CACHE_TTL_SECONDS


def test_a_cache_hit_skips_the_analysis_service_but_echoes_the_callers_hash(valkey_off: None) -> None:
    cached = {**CLEAN, "content_hash": "hash-of-whoever-primed-the-cache"}
    request = AnalyseRequest(content=REQUEST.content, content_hash="my-hash")
    with (
        patch("fia_api.core.services.script_validation.cache_get_json", return_value=cached),
        patch("requests.post") as post,
    ):
        result = analyse_script_for_user(request, user_number=1234)

    assert result.status_code == HTTPStatus.OK
    assert result.body["content_hash"] == "my-hash"
    assert result.body["diagnostics"] == []
    post.assert_not_called()


@pytest.mark.parametrize(
    ("upstream_status", "upstream_body"),
    [
        (HTTPStatus.SERVICE_UNAVAILABLE, {"detail": {"reason": "warming_up"}}),
        (HTTPStatus.OK, {"detail": "shaped nothing like an analysis result"}),
    ],
)
def test_only_a_well_formed_ok_result_is_cached(
    valkey_off: None,
    upstream_status: int,
    upstream_body: dict[str, object],
) -> None:
    """Caching a 503 would keep the editor reading a warm service as cold for the whole TTL."""
    upstream = _upstream(status=upstream_status, body=upstream_body)
    with (
        patch("fia_api.core.services.script_validation.cache_get_json", return_value=None),
        patch("fia_api.core.services.script_validation.cache_set_json") as cache_set,
        patch("requests.post", return_value=upstream),
    ):
        analyse_script_for_user(REQUEST, user_number=1234)

    cache_set.assert_not_called()


def test_an_upstream_timeout_becomes_504(cache_empty: Mock, valkey_off: None) -> None:
    with patch(
        "requests.post",
        side_effect=requests.Timeout("too slow"),
    ):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.GATEWAY_TIMEOUT
    assert result.body["detail"]["reason"] == "timed_out"


def test_an_unreachable_service_becomes_503(cache_empty: Mock, valkey_off: None) -> None:
    with patch(
        "requests.post",
        side_effect=requests.ConnectionError("no route to host"),
    ):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert result.body["detail"]["reason"] == "upstream_unavailable"


def test_a_non_json_response_becomes_502(cache_empty: Mock, valkey_off: None) -> None:
    upstream = Mock()
    upstream.status_code = HTTPStatus.BAD_GATEWAY
    upstream.json.side_effect = ValueError("not json")
    with patch("requests.post", return_value=upstream):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.BAD_GATEWAY
    assert result.body["detail"]["reason"] == "bad_upstream_response"


def test_a_non_object_json_body_is_wrapped_in_detail_rather_than_dropped(cache_empty: Mock, valkey_off: None) -> None:
    """The contract says the body is an object; if that ever changes upstream, keep the payload rather
    than 500 on an unexpected shape."""
    with patch("requests.post", return_value=_upstream(body=[1, 2, 3])):
        result = analyse_script_for_user(REQUEST, user_number=1234)

    assert result.status_code == HTTPStatus.OK
    assert result.body == {"detail": [1, 2, 3]}


# --- the route --------------------------------------------------------------------------------------


def _jwt_headers(payload: dict[str, object]) -> dict[str, str]:
    token = jwt.encode(payload, "test-signing-key-with-at-least-32-bytes", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, valkey_off: None) -> Iterator[TestClient]:
    """A client with auth live and nothing cached, leaving the analysis service call to the test."""
    monkeypatch.setenv("FIA_API_API_KEY", API_KEY)
    monkeypatch.setattr("fia_api.core.auth.tokens.DEV_MODE", False)
    with (
        patch("fia_api.core.services.script_validation.cache_get_json", return_value=None),
        patch("fia_api.core.services.script_validation.cache_set_json"),
        TestClient(app) as test_client,
    ):
        yield test_client


@contextmanager
def analysis_service(status: int = HTTPStatus.OK, body: object = BROKEN) -> Iterator[Mock]:
    """Stand in for mantid-python-script-lsp.

    Patched on `requests.post` itself rather than on the copy imported into this service's module, because
    the JWT bearer calls `requests.post` too and both modules share the one module object: patching the two
    separately means the second patch silently replaces the first, and the auth stub then sees editor
    traffic. JWT tests stub `_is_jwt_access_token_valid` instead, leaving `requests.post` free for this.
    """
    with patch("requests.post", return_value=_upstream(status=status, body=body)) as post:
        yield post


def test_the_route_requires_authentication(client: TestClient) -> None:
    """`JWTAPIBearer` inherits `HTTPBearer(auto_error=True)`, which answers 401 with no header at all;
    a present-but-invalid token is a 403 from `authentication_error_handler`, covered below."""
    response = client.post("/script/analyse", json={"content": "x = 1\n", "content_hash": "h"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_a_jwt_user_can_analyse_a_script(client: TestClient) -> None:
    headers = _jwt_headers({"usernumber": 1234, "role": "user"})
    with (
        patch.object(JWTAPIBearer, "_is_jwt_access_token_valid", return_value=True),
        analysis_service() as post,
    ):
        response = client.post(
            "/script/analyse",
            json={"content": REQUEST.content, "content_hash": "hash-1"},
            headers=headers,
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == BROKEN
    assert post.call_args.args[0].endswith("/analyse")
    assert post.call_args.kwargs["json"] == {"content": REQUEST.content, "content_hash": "hash-1"}


def test_a_rejected_jwt_never_reaches_the_analysis_service(client: TestClient) -> None:
    headers = _jwt_headers({"usernumber": 1234, "role": "user"})
    with (
        patch.object(JWTAPIBearer, "_is_jwt_access_token_valid", return_value=False),
        analysis_service() as post,
    ):
        response = client.post(
            "/script/analyse",
            json={"content": "x = 1\n", "content_hash": "h"},
            headers=headers,
        )

    assert response.status_code == HTTPStatus.FORBIDDEN
    post.assert_not_called()


def test_a_warming_service_still_answers_503_through_the_route(client: TestClient) -> None:
    """The status has to survive the route: the editor only says "still starting up" because of it."""
    warming = {"detail": {"reason": "warming_up", "detail": "Loading the Mantid framework"}}
    with analysis_service(status=HTTPStatus.SERVICE_UNAVAILABLE, body=warming):
        response = client.post(
            "/script/analyse",
            json={"content": REQUEST.content, "content_hash": "hash-1"},
            headers={"Authorization": f"Bearer {API_KEY}"},
        )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == warming


def test_an_oversized_script_is_refused_before_the_service_is_called(client: TestClient) -> None:
    with cap_at(CAP_BYTES), analysis_service() as post:
        response = client.post(
            "/script/analyse",
            json={"content": EMOJI * 3, "content_hash": "too-big"},
            headers={"Authorization": f"Bearer {API_KEY}"},
        )

    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert response.json() == {
        "detail": {"reason": "too_large", "limit_bytes": CAP_BYTES, "actual_bytes": len((EMOJI * 3).encode())}
    }
    post.assert_not_called()


def test_a_rate_limited_user_gets_retry_after(client: TestClient) -> None:
    over_limit = Mock()
    over_limit.incr.return_value = RATE_LIMIT_MAX_REQUESTS + 1
    with (
        patch("fia_api.core.services.script_validation.get_valkey_client", return_value=over_limit),
        analysis_service() as post,
    ):
        response = client.post(
            "/script/analyse",
            json={"content": "x = 1\n", "content_hash": "h"},
            headers={"Authorization": f"Bearer {API_KEY}"},
        )

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json()["detail"]["reason"] == "rate_limited"
    assert 0 < int(response.headers["retry-after"]) <= RATE_LIMIT_WINDOW_SECONDS
    post.assert_not_called()
