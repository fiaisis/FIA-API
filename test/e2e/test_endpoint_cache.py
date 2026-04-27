"""Cache behavior tests for live-data and instrument endpoints."""

from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.fia_api import app

from .constants import STAFF_HEADER

client = TestClient(app)


# --- GET /live-data/instruments ---


@patch("fia_api.routers.live_data.LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS", 120)
@patch("fia_api.routers.live_data.get_instruments_with_live_data_support")
@patch("fia_api.routers.live_data.cache_set_json")
@patch("fia_api.routers.live_data.cache_get_json")
def test_live_data_instruments_cache_hit(mock_cache_get, mock_cache_set, mock_get_instruments):
    cached_payload = ["INSTRUMENT_1", "INSTRUMENT_2"]
    mock_cache_get.return_value = cached_payload

    response = client.get("/live-data/instruments")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_payload
    mock_get_instruments.assert_not_called()
    mock_cache_set.assert_not_called()


# --- GET /live-data/{instrument}/script ---


@patch("fia_api.routers.live_data.LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS", 60)
@patch("fia_api.routers.live_data.get_live_data_script_by_instrument_name")
@patch("fia_api.routers.live_data.cache_set_json")
@patch("fia_api.routers.live_data.cache_get_json")
def test_live_data_script_cache_hit(mock_cache_get, mock_cache_set, mock_get_script):
    mock_cache_get.return_value = {"script": "print('hello')"}

    response = client.get("/live-data/TEST/script")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == "print('hello')"
    mock_get_script.assert_not_called()
    mock_cache_set.assert_not_called()


@patch("fia_api.routers.live_data.LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS", 60)
@patch("fia_api.routers.live_data.get_live_data_script_by_instrument_name")
@patch("fia_api.routers.live_data.cache_set_json")
@patch("fia_api.routers.live_data.cache_get_json")
def test_live_data_script_cache_hit_none_script(mock_cache_get, mock_cache_set, mock_get_script):
    """A cached None script (instrument has no script) should still be a cache hit."""
    mock_cache_get.return_value = {"script": None}

    response = client.get("/live-data/TEST/script")

    assert response.status_code == HTTPStatus.OK
    assert response.json() is None
    mock_get_script.assert_not_called()
    mock_cache_set.assert_not_called()


# --- GET /instrument/{instrument_name}/specification ---


@patch("fia_api.routers.instrument_specs.INSTRUMENT_SPEC_CACHE_TTL_SECONDS", 120)
@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.routers.instrument_specs.get_specification_by_instrument_name")
@patch("fia_api.routers.instrument_specs.cache_set_json")
@patch("fia_api.routers.instrument_specs.cache_get_json")
def test_instrument_spec_cache_hit(mock_cache_get, mock_cache_set, mock_get_spec, mock_post):
    cached_spec = {"foo": "bar", "baz": 42}
    mock_cache_get.return_value = {"specification": cached_spec}
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/instrument/TEST/specification", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_spec
    mock_get_spec.assert_not_called()
    mock_cache_set.assert_not_called()


# --- GET /instrument/{instrument}/latest-run ---


@patch("fia_api.routers.instrument.INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS", 15)
@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.routers.instrument.get_latest_run_by_instrument_name")
@patch("fia_api.routers.instrument.cache_set_json")
@patch("fia_api.routers.instrument.cache_get_json")
def test_instrument_latest_run_cache_hit(mock_cache_get, mock_cache_set, mock_get_latest, mock_post):
    cached_payload = {"latest_run": "12345"}
    mock_cache_get.return_value = cached_payload
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/instrument/TEST/latest-run", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_payload
    mock_get_latest.assert_not_called()
    mock_cache_set.assert_not_called()
