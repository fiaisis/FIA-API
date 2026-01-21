"""Tests for cache helpers."""

import json

import os
from unittest.mock import Mock, patch
from redis.exceptions import RedisError

from fia_api.core.cache import (
    _create_client,
    _valkey_configured,
    _valkey_state,
    cache_get_json,
    cache_set_json,
    get_valkey_client,
    hash_key,
)

TTL_SECONDS = 30


def test_cache_get_json_returns_none_when_no_client():
    with patch("fia_api.core.cache.get_valkey_client", return_value=None) as mock_client:
        assert cache_get_json("key") is None
        mock_client.assert_called_once_with()


def test_cache_get_json_returns_parsed_payload():
    mock_client = Mock()
    mock_client.get.return_value = '{"answer": 42}'
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") == {"answer": 42}
        mock_client.get.assert_called_once_with("key")


def test_cache_get_json_returns_none_for_bad_json():
    mock_client = Mock()
    mock_client.get.return_value = "not-json"
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") is None


def test_cache_set_json_sets_payload_with_ttl():
    mock_client = Mock()
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        cache_set_json("key", {"answer": 42}, TTL_SECONDS)
        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        assert args[0] == "key"
        assert args[1] == TTL_SECONDS
        assert json.loads(args[2]) == {"answer": 42}


def test_cache_set_json_noop_for_bad_payload():
    mock_client = Mock()
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        cache_set_json("key", object(), TTL_SECONDS)
        mock_client.setex.assert_not_called()


def test_cache_set_json_noop_for_non_positive_ttl():
    with patch("fia_api.core.cache.get_valkey_client") as mock_client:
        cache_set_json("key", {"answer": 42}, 0)
        mock_client.assert_not_called()



def test_valkey_configured_false():
    with patch.dict(os.environ, {}, clear=True):
        assert _valkey_configured() is False


def test_valkey_configured_true():
    with patch.dict(os.environ, {"VALKEY_URL": "redis://localhost"}, clear=True):
        assert _valkey_configured() is True
    with patch.dict(os.environ, {"VALKEY_HOST": "localhost"}, clear=True):
        assert _valkey_configured() is True



def test_create_client_with_url():
    with (
        patch.dict(os.environ, {"VALKEY_URL": "redis://localhost"}, clear=True),
        patch("fia_api.core.cache.Redis.from_url") as mock_from_url,
    ):
        _create_client()
        mock_from_url.assert_called_once()


def test_create_client_with_params():
    env = {
        "VALKEY_HOST": "localhost",
        "VALKEY_PORT": "6379",
        "VALKEY_DB": "0",
        "VALKEY_PASSWORD": "pass",
        "VALKEY_SSL": "true",
    }
    with patch.dict(os.environ, env, clear=True):
        with patch("fia_api.core.cache.Redis") as mock_redis:
            _create_client()
            mock_redis.assert_called_once()
            _, kwargs = mock_redis.call_args
            assert kwargs["host"] == "localhost"
            assert kwargs["ssl"] is True


def test_create_client_no_host():
    with patch.dict(os.environ, {}, clear=True):
        assert _create_client() is None


def test_get_valkey_client_disabled():
    with patch("fia_api.core.cache._valkey_state") as mock_state_func:
        mock_state = Mock()
        mock_state.disabled = True
        mock_state_func.return_value = mock_state
        assert get_valkey_client() is None


def test_get_valkey_client_not_configured():
    with patch("fia_api.core.cache._valkey_state") as mock_state_func:
        mock_state = Mock()
        mock_state.disabled = False
        mock_state_func.return_value = mock_state
        with patch("fia_api.core.cache._valkey_configured", return_value=False):
            assert get_valkey_client() is None


def test_get_valkey_client_creation_error():
    with patch("fia_api.core.cache._valkey_state") as mock_state_func:
        mock_state = Mock()
        mock_state.disabled = False
        mock_state.client = None
        mock_state_func.return_value = mock_state

        with (
            patch("fia_api.core.cache._valkey_configured", return_value=True),
            patch("fia_api.core.cache._create_client", side_effect=RedisError("boom")),
        ):
            assert get_valkey_client() is None
            assert mock_state.disabled is True


def test_cache_get_json_redis_error():
    mock_client = Mock()
    mock_client.get.side_effect = RedisError("boom")
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") is None


def test_cache_get_json_bytes():
    mock_client = Mock()
    mock_client.get.return_value = b'{"answer": 42}'
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") == {"answer": 42}


def test_cache_get_json_unknown_type():
    mock_client = Mock()
    mock_client.get.return_value = 123  # Not bytes or str
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") is None


def test_cache_set_json_client_none():
    with patch("fia_api.core.cache.get_valkey_client", return_value=None):
        cache_set_json("key", {}, TTL_SECONDS)
        # Should just return without error


def test_cache_set_json_redis_error():
    mock_client = Mock()
    mock_client.setex.side_effect = RedisError("boom")
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        cache_set_json("key", {}, TTL_SECONDS)
        # Should check if cache got disabled
        # We can mock _disable_cache to verify it IS called

    with (
        patch("fia_api.core.cache.get_valkey_client", return_value=mock_client),
        patch("fia_api.core.cache._disable_cache") as mock_disable,
    ):
        cache_set_json("key", {}, TTL_SECONDS)
        mock_disable.assert_called_once()


def test_get_valkey_client_returns_existing_client():
    with patch("fia_api.core.cache._valkey_state") as mock_state_func:
        mock_state = Mock()
        mock_state.disabled = False
        existing_client = Mock()
        mock_state.client = existing_client
        mock_state_func.return_value = mock_state

        with patch("fia_api.core.cache._valkey_configured", return_value=True):
            assert get_valkey_client() is existing_client
            # Should NOT call _create_client
            with patch("fia_api.core.cache._create_client") as mock_create:
                get_valkey_client()
                mock_create.assert_not_called()


def test_cache_get_json_returns_none_if_raw_is_none():
    mock_client = Mock()
    mock_client.get.return_value = None
    with patch("fia_api.core.cache.get_valkey_client", return_value=mock_client):
        assert cache_get_json("key") is None


def test_hash_key_returns_sha256_hex():
    assert hash_key("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
