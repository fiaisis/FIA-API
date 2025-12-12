# Test for instrument latest runs
from http import HTTPStatus
from unittest.mock import patch

from sqlalchemy import select

from fia_api.core.models import Instrument
from test.e2e.constants import STAFF_HEADER, USER_HEADER
from test.e2e.test_core import client
from utils.db_generator import SESSION


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_latest_run(mock_post):
    """
    Test correct latest run for instrument returned
    :return:
    """
    with SESSION() as session:
        expected_latest_run = session.scalar(select(Instrument).where(Instrument.instrument_name == "LET")).latest_run

    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/let/latest-run", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"latest_run": expected_latest_run}


def test_get_instrument_latest_run_no_jwt_returns_403():
    """
    Test that getting latest run without JWT returns 403
    :return:
    """
    response = client.get("/instrument/het/latest-run")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_latest_run_user_token_returns_403(mock_post):
    """Test that getting latest run with non staff token returns 403"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/het/latest-run", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_latest_run_with_user_token_returns_403(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    """Test that putting latest run with non staff token returns 403"""
    response = client.put("/instrument/het/latest-run", json={"latest_run": "75827"}, headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_instrument_latest_run_bad_jwt():
    """
    Test that getting latest run with bad JWT returns 403
    :return:
    """
    response = client.get("/instrument/het/latest-run", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_latest_run(mock_post):
    """Test instrument latest run is updated"""
    mock_post.return_value.status_code = HTTPStatus.OK
    client.put("/instrument/tosca/latest-run", json={"latest_run": "54321"}, headers=STAFF_HEADER)
    response = client.get("/instrument/tosca/latest-run", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"latest_run": "54321"}
