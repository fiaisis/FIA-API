"""Valkey cache helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

_VALKEY_CLIENT: Redis | None = None
_VALKEY_DISABLED = False


def _valkey_configured() -> bool:
    return bool(os.environ.get("VALKEY_URL") or os.environ.get("VALKEY_HOST"))


def _create_client() -> Redis | None:
    url = os.environ.get("VALKEY_URL")
    if url:
        return Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=1,
            retry_on_timeout=False,
        )

    host = os.environ.get("VALKEY_HOST")
    if not host:
        return None

    port = int(os.environ.get("VALKEY_PORT", "6379"))
    db = int(os.environ.get("VALKEY_DB", "0"))
    password = os.environ.get("VALKEY_PASSWORD")
    ssl_enabled = os.environ.get("VALKEY_SSL", "").lower() in ("1", "true", "yes")
    return Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        ssl=ssl_enabled,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=1,
        retry_on_timeout=False,
    )


def get_valkey_client() -> Redis | None:
    global _VALKEY_CLIENT, _VALKEY_DISABLED
    if _VALKEY_DISABLED:
        return None
    if not _valkey_configured():
        return None
    if _VALKEY_CLIENT is None:
        try:
            _VALKEY_CLIENT = _create_client()
        except (RedisError, ValueError) as exc:
            _VALKEY_DISABLED = True
            logger.warning("Valkey cache disabled: %s", exc)
            return None
    return _VALKEY_CLIENT


def _disable_cache(exc: Exception) -> None:
    global _VALKEY_DISABLED
    if not _VALKEY_DISABLED:
        _VALKEY_DISABLED = True
        logger.warning("Valkey cache disabled: %s", exc)


def cache_get_json(key: str) -> Any | None:
    client = get_valkey_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
    except RedisError as exc:
        _disable_cache(exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    client = get_valkey_client()
    if client is None:
        return
    try:
        payload = json.dumps(value)
    except TypeError:
        return
    try:
        client.setex(key, ttl_seconds, payload)
    except RedisError as exc:
        _disable_cache(exc)


def hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
