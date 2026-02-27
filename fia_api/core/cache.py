"""Valkey cache helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from functools import cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

DEFAULT_VALKEY_URL = "redis://valkey.valkey.svc.cluster.local:6379/0"


@dataclass(slots=True)
class _ValkeyState:
    client: Redis | None = None
    disabled: bool = False


@cache
def _valkey_state() -> _ValkeyState:
    return _ValkeyState()


def _create_client() -> Redis | None:
    url = os.environ.get("VALKEY_URL", DEFAULT_VALKEY_URL)
    return Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=1,
        retry_on_timeout=False,
    )


def get_valkey_client() -> Redis | None:
    """
    Get or create a Valkey (Redis) client instance.

    Returns a shared Redis client if Valkey is available.
    The client is lazily initialized on first access and cached for reuse.
    If the connection fails, it returns None and disables further connection
    attempts.

    :return: Redis client instance if available, None otherwise
    """

    state = _valkey_state()
    if state.disabled:
        logger.warning("Valkey cache disabled: previous connection error")
        return None
    if state.client is None:
        try:
            state.client = _create_client()
        except (RedisError, ValueError) as exc:
            state.disabled = True
            logger.warning("Valkey cache disabled: %s", exc)
            return None
    return state.client


def _disable_cache(exc: Exception) -> None:
    state = _valkey_state()
    if not state.disabled:
        state.disabled = True
        logger.warning("Valkey cache disabled: %s", exc)


def cache_get_json(key: str) -> Any | None:
    """
    Retrieve and deserialize a JSON value from the Valkey cache.

    Attempts to fetch a cached value by key and parse it as JSON. If the cache
    is unavailable, the key doesn't exist, or the value cannot be parsed as JSON,
    returns None. Automatically disables the cache on connection errors.

    :param key: The cache key to retrieve
    :return: Deserialized JSON value if found and valid, None otherwise
    """

    client = get_valkey_client()
    if client is None:
        logger.warning("Failed to retrieve JSON from Valkey cache (cache disabled)")
        return None
    try:
        raw = client.get(key)
    except RedisError as exc:
        _disable_cache(exc)
        logger.exception("Failed to retrieve JSON from Valkey cache", exc_info=exc)
        return None
    if raw is None:
        logger.warning("No value found in Valkey cache for key: %s", key)
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw_text = raw.decode("utf-8")
    elif isinstance(raw, str):
        raw_text = raw
    else:
        return None
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from Valkey cache")
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    """
    Store a JSON-serializable value in the Valkey cache with a time-to-live.

    Serializes the provided value to JSON and stores it in the cache with an
    expiration time. If the cache is unavailable, the value cannot be serialized
    to JSON, or the TTL is non-positive, the operation is silently skipped.
    Automatically disables the cache on connection errors.

    :param key: The cache key under which to store the value
    :param value: Any JSON-serializable value to cache
    :param ttl_seconds: Time-to-live in seconds; must be positive
    :return: None
    """

    if ttl_seconds <= 0:
        return
    client = get_valkey_client()
    if client is None:
        logger.warning("Failed to set JSON in Valkey cache (cache disabled)")
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
    """
    Generate a SHA-256 hash of the input string.

    Computes a hexadecimal SHA-256 digest of the UTF-8 encoded input string.
    Useful for creating deterministic cache keys from arbitrary string data.

    :param value: The string to hash
    :return: Hexadecimal SHA-256 digest as a string
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
