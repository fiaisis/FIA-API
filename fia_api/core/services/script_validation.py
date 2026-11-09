"""Service layer for forwarding script analysis requests to mantid-python-script-lsp."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final, TypeGuard

import requests
from redis.exceptions import RedisError

from fia_api.core.cache import cache_get_json, cache_set_json, get_valkey_client, hash_key
from fia_api.core.request_models import AnalyseRequest

logger = logging.getLogger(__name__)

SCRIPT_LSP_URL = os.environ.get("SCRIPT_LSP_URL", "http://mantid-python-script-lsp-service.fia.svc.cluster.local:80")

#: Measured in UTF-8 bytes rather than characters, and has to mean the same thing here as it does in
#: mantid-python-script-lsp, or a script passes one service and is refused by the other.
MAX_SCRIPT_BYTES = int(os.environ.get("MAX_SCRIPT_BYTES", "200000"))

#: Analysis is advisory and runs on every debounced edit, so it must never make the editor wait.
SCRIPT_ANALYSE_TIMEOUT_SECONDS: Final = 5.0
SCRIPT_ANALYSE_CACHE_TTL_SECONDS = int(os.environ.get("SCRIPT_ANALYSE_CACHE_TTL_SECONDS", "600"))

#: The frontend debounces to one request per second per editor, so this leaves several times headroom.
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("SCRIPT_ANALYSE_RATE_LIMIT_MAX_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("SCRIPT_ANALYSE_RATE_LIMIT_WINDOW_SECONDS", "10"))

logger.info(
    "Script analysis: %s; %s bytes; %.1fs timeout; cache %ss; %s requests per %ss",
    SCRIPT_LSP_URL,
    MAX_SCRIPT_BYTES,
    SCRIPT_ANALYSE_TIMEOUT_SECONDS,
    SCRIPT_ANALYSE_CACHE_TTL_SECONDS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)


@dataclass(frozen=True)
class UpstreamAnalysisResult:
    """Status code and JSON body to forward to the frontend."""

    status_code: int
    body: dict[str, Any]
    retry_after_seconds: int | None = None


def _cache_key(content: str) -> str:
    return f"script_analyse:v1:{hash_key(content)}"


def check_rate_limit(user_number: int) -> int | None:
    """
    Record one script analysis request for a user in a fixed Valkey window.

    Returns the number of seconds until the window resets when the user is over the limit, or `None`
    when the request is allowed. Valkey being down fails open rather than refusing to validate: the
    endpoint is advisory and the service it fronts is already rate-limited on its own side.
    """
    client = get_valkey_client()
    if client is None:
        return None

    window = int(time.time() // RATE_LIMIT_WINDOW_SECONDS)
    key = f"script_analyse_rate:v1:{user_number}:{window}"
    try:
        count = client.incr(key)
        if count == 1:
            client.expire(key, RATE_LIMIT_WINDOW_SECONDS)
    except RedisError as exc:
        logger.warning("Script analysis rate limit check failed, allowing the request through: %s", exc)
        return None

    if count > RATE_LIMIT_MAX_REQUESTS:
        return RATE_LIMIT_WINDOW_SECONDS - int(time.time() % RATE_LIMIT_WINDOW_SECONDS)
    return None


def _refuse_before_analysis(request: AnalyseRequest, user_number: int) -> UpstreamAnalysisResult | None:
    """The two refusals that cost nothing to make: an oversized script, and a user over their rate limit."""
    size = len(request.content.encode("utf-8"))
    if size > MAX_SCRIPT_BYTES:
        # Refused here in the shape mantid-python-script-lsp uses for the same refusal, so the editor
        # sees one answer for "too big" no matter which side caught it. Also keeps a multi-megabyte
        # script from reaching Valkey or a worker at all.
        return UpstreamAnalysisResult(
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            body={"detail": {"reason": "too_large", "limit_bytes": MAX_SCRIPT_BYTES, "actual_bytes": size}},
        )

    retry_after = check_rate_limit(user_number)
    if retry_after is not None:
        return UpstreamAnalysisResult(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            body={"detail": {"reason": "rate_limited", "message": "Too many script analysis requests"}},
            retry_after_seconds=retry_after,
        )

    return None


def analyse_script_for_user(request: AnalyseRequest, user_number: int) -> UpstreamAnalysisResult:
    """
    Analyse a script with mantid-python-script-lsp, rate limited per user and cached in Valkey.

    FIA-API models only `AnalyseRequest`; the upstream status code and JSON body are forwarded
    unchanged so the frontend can tell `200` from `413`, `422`, `429`, `503`, and `504`.
    """
    refused = _refuse_before_analysis(request, user_number)
    if refused is not None:
        return refused

    cache_key = _cache_key(request.content)
    cached = cache_get_json(cache_key)
    if _is_analysis_result(cached):
        # Results are cached by content hash, which is shared across users: echo the caller's own hash
        # back so the frontend's stale-response check still works.
        return UpstreamAnalysisResult(status_code=HTTPStatus.OK, body={**cached, "content_hash": request.content_hash})

    url = f"{SCRIPT_LSP_URL.rstrip('/')}/analyse"
    try:
        response = requests.post(url, json=request.model_dump(), timeout=SCRIPT_ANALYSE_TIMEOUT_SECONDS)
    except requests.Timeout:
        logger.warning("Script analysis timed out after %ss", SCRIPT_ANALYSE_TIMEOUT_SECONDS)
        return UpstreamAnalysisResult(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            body={
                "detail": {
                    "reason": "timed_out",
                    "message": f"Script analysis took longer than {SCRIPT_ANALYSE_TIMEOUT_SECONDS} seconds",
                }
            },
        )
    except requests.RequestException as exc:
        logger.warning("Failed to reach mantid-python-script-lsp at %s: %s", url, exc)
        return UpstreamAnalysisResult(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            body={"detail": {"reason": "upstream_unavailable", "message": "Script analysis service unavailable"}},
        )

    try:
        payload = response.json()
    except ValueError:
        logger.warning("mantid-python-script-lsp returned non-JSON with status %s", response.status_code)
        return UpstreamAnalysisResult(
            status_code=HTTPStatus.BAD_GATEWAY,
            body={"detail": {"reason": "bad_upstream_response", "message": "Invalid response from analysis service"}},
        )

    body: dict[str, Any] = payload if isinstance(payload, dict) else {"detail": payload}
    if response.status_code == HTTPStatus.OK and _is_analysis_result(body):
        cache_set_json(cache_key, body, SCRIPT_ANALYSE_CACHE_TTL_SECONDS)

    return UpstreamAnalysisResult(status_code=response.status_code, body=body)


def _is_analysis_result(value: object) -> TypeGuard[dict[str, Any]]:
    """True if `value` looks like an `AnalysisResponse` from mantid-python-script-lsp."""
    return isinstance(value, dict) and "parses" in value and "diagnostics" in value
