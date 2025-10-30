import os
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from test.e2e.constants import STAFF_HEADER
from test.e2e.test_core import client


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_get_instrument(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(
        "/find_file/instrument/MARI/experiment_number/20024?filename=MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER
    )

    assert response.status_code == HTTPStatus.OK
    assert response.text == '"MARI/RBNumber/RB20024/autoreduced/MAR29531_10.5meV_sa.nxspe"'


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_get_instrument_file_not_found(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(
        "/find_file/instrument/MARI/experiment_number/20024?filename=MAR12345.nxspe", headers=STAFF_HEADER
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_get_instrument_file_no_perms(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN

    response = client.get("/find_file/instrument/MARI/experiment_number/20024?filename=MAR29531_10.5meV_sa.nxspe")

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_experiment_number(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(
        "/find_file/generic/experiment_number/20024?filename=MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER
    )

    assert response.status_code == HTTPStatus.OK
    assert response.text == '"GENERIC/autoreduce/ExperimentNumbers/20024/MAR29531_10.5meV_sa.nxspe"'


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_experiment_number_not_found(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/find_file/generic/experiment_number/20024?filename=MAR12345.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_experiment_number_no_perms(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN

    response = client.get("/find_file/generic/experiment_number/20024?filename=MAR29531_10.5meV_sa.nxspe")

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_user_number(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(
        "/find_file/generic/user_number/20024?filename=MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER
    )

    assert response.status_code == HTTPStatus.OK
    assert response.text == '"GENERIC/autoreduce/UserNumbers/20024/MAR29531_10.5meV_sa.nxspe"'


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_user_number_not_found(mock_post):
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/find_file/generic/user_number/20024?filename=MAR12345.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("fia_api.core.auth.tokens.requests.post")
def test_find_file_generic_user_number_no_perms(mock_post):
    os.environ["CEPH_DIR"] = str(Path(__file__ + "../test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN

    response = client.get("/find_file/generic/user_number/20024?filename=MAR29531_10.5meV_sa.nxspe")

    assert response.status_code == HTTPStatus.FORBIDDEN
