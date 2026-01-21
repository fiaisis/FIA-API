"""Tests for cache helpers."""

import json
from unittest.mock import Mock, patch

from fia_api.core.cache import cache_get_json, cache_set_json, hash_key

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


def test_hash_key_returns_sha256_hex():
    assert hash_key("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
