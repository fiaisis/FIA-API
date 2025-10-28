from http import HTTPStatus

from test.e2e.test_core import client


def test_liveness_probes():
    """
    Test endpoint for probes
    :return: None
    """
    response = client.get("/healthz")
    assert response.status_code == HTTPStatus.OK
    assert response.text == '"ok"'


def test_readiness_probes():
    """
    Test endpoint for probes
    :return: None
    """
    response = client.get("/ready")
    assert response.status_code == HTTPStatus.OK
    assert response.text == '"ok"'
