from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from fia_api.fia_api import app

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def producer_channel():
    """Consume producer channel fixture"""


def test_get_instrument_specification():
    mock_specification = {
        "name": "test_instrument",
        "enabled": "true",
    }

    response = client.get(
        f"/instrument/{mock_specification["name"]}/specification",
        headers={"Authorization": "Bearer shh"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == mock_specification
