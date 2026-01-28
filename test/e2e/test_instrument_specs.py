# Test instrument specification endpoints
from http import HTTPStatus
from unittest.mock import patch

from sqlalchemy import select

from fia_api.core.models import Instrument
from test.e2e.constants import STAFF_HEADER
from test.e2e.test_core import client
from utils.db_generator import SESSION


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_specification(mock_post):
    """
    Test correct spec for instrument returned
    :return:
    """
    with SESSION() as session:
        expected_spec = session.scalar(select(Instrument).where(Instrument.instrument_name == "HET")).specification
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/het/specification", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == expected_spec


def test_get_instrument_specification_no_jwt_returns_403():
    """
    Test correct spec for instrument returned
    :return:
    """
    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_instrument_specification_bad_jwt():
    """
    Test correct spec for instrument returned
    :return:
    """
    response = client.get("/instrument/het/specification", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_specification(mock_post):
    """Test instrument put is updated"""
    mock_post.return_value.status_code = HTTPStatus.OK
    client.put("/instrument/tosca/specification", json={"foo": "bar"}, headers=STAFF_HEADER)
    response = client.get("/instrument/tosca/specification", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"foo": "bar"}


def test_put_instrument_specification_no_api_key():
    """Test instrument put is updated"""
    client.put("/instrument/het/specification", json={"foo": "bar"})
    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_instruments_with_live_data_support():
    """Test getting instruments with live data support returns expected list"""
    with SESSION() as session:
        expected_instruments = [
            inst.instrument_name
            for inst in session.scalars(select(Instrument).where(Instrument.live_data_support.is_(True)))
        ]
    response = client.get("/live-data/instruments")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == expected_instruments


def test_get_instruments_with_live_data_support_after_enabling():
    """Test that an instrument appears in the list after enabling live data support"""
    with SESSION() as session:
        # Enable live data support for MARI
        instrument = session.scalar(select(Instrument).where(Instrument.instrument_name == "MARI"))
        original_value = instrument.live_data_support
        instrument.live_data_support = True
        session.commit()

    try:
        response = client.get("/live-data/instruments")
        assert response.status_code == HTTPStatus.OK
        assert "MARI" in response.json()
    finally:
        # Revert the change
        with SESSION() as session:
            instrument = session.scalar(select(Instrument).where(Instrument.instrument_name == "MARI"))
            instrument.live_data_support = original_value
            session.commit()
