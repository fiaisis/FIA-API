import os
import random
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from fia_api.fia_api import app

from .constants import STAFF_HEADER, USER_HEADER

client = TestClient(app)


@pytest.fixture()
def mock_file():
    file_names = ["test_file_1.txt", "test_file_2.png"]
    files = {
        0: (file_names[0], b"Insert file content here", "text/plain"),
        1: (file_names[1], b"Yet another file", "text/plain"),
    }
    return files[random.randint(0, 1)]  # noqa: S311


@pytest.fixture(autouse=True)
def _setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("EXTRAS_DIRECTORY", str(tmp_path))


@pytest.fixture()
def _setup_inst_folder(tmp_path):
    for instrument_folder in sorted(instrument_folders):
        path = tmp_path / instrument_folder
        path.mkdir(parents=True, exist_ok=True)


instrument_folders = [
    "alf",
    "argus",
    "chipir",
    "chronus",
    "crisp",
    "emu",
    "enginx",
    "gem",
    "hifi",
    "hrpd",
    "imat",
    "ines",
    "inter",
    "iris",
    "larmor",
    "let",
    "loq",
    "maps",
    "mari",
    "merlin",
    "musr",
    "nimrod",
    "offspec",
    "osiris",
    "pearl",
    "polaris",
    "polref",
    "sandals",
    "sans2d",
    "surf",
    "sxd",
    "tosca",
    "vesuvio",
    "wish",
    "zoom",
]


@pytest.mark.usefixtures("_setup_inst_folder")
@patch("fia_api.core.auth.tokens.requests.post")
def test_read_extras_populated(mock_post, tmp_path):
    """Tests the root folders is populated (instrument folders exist)"""
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/extras", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == instrument_folders


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_extras_empty(mock_post):
    """Tests the root folder is empty"""
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/extras", headers=STAFF_HEADER)
    folders = response.json()
    assert folders == []
    assert response.status_code == HTTPStatus.OK


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_extras_no_jwt_returns_forbidden(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/extras")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_extras_user_jwt_returns_forbidden(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/extras", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_setup_inst_folder")
@patch("fia_api.core.auth.tokens.requests.post")
def test_read_instrument_empty(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK

    """Tests that a randomly selected instrument folder is empty"""
    response = client.get(f"/extras/{instrument_folders[0]}", headers=STAFF_HEADER)
    instrument_files = response.json()
    assert instrument_files == []
    assert response.status_code == HTTPStatus.OK


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_instrument_populated(mock_post):
    """Tests if files under instrument folder are read correctly"""
    mock_post.return_value.status_code = HTTPStatus.OK
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    # Insert two files (creating directories and files)
    file_directory = Path(root_folder / instrument_folders[2]) / "filename1"
    file_directory2 = Path(root_folder / instrument_folders[2]) / "filename2"
    file_directory.mkdir(parents=True, exist_ok=True)
    Path.touch(file_directory)
    Path.touch(file_directory2)
    # check contents of the instrument folder
    response = client.get(f"/extras/{instrument_folders[2]}", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == sorted([str(file_directory.stem), str(file_directory2.stem)])


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_instrument_fails_no_jwt(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(f"/extras/{instrument_folders[2]}")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_read_instrument_fails_user_jwt(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(f"/extras/{instrument_folders[2]}", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_setup_inst_folder")
@patch("fia_api.core.auth.tokens.requests.post")
def test_success_file_upload(mock_post, mock_file):
    """Tests if files are uploaded successfully"""
    mock_post.return_value.status_code = HTTPStatus.OK

    upload_file = {"file": mock_file}
    upload_url = f"/extras/{instrument_folders[3]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file, headers=STAFF_HEADER)

    assert response.json() == f"Successfully uploaded {mock_file[0]}"
    assert response.status_code == HTTPStatus.OK


@patch("fia_api.core.auth.tokens.requests.post")
def test_file_upload_fails_with_forbidden_no_jwt(mock_post, mock_file):
    mock_post.return_value.status_code = HTTPStatus.OK

    upload_file = {"file": mock_file}
    upload_url = f"/extras/{instrument_folders[3]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_file_upload_fails_with_forbidden_user_jwt(mock_post, mock_file):
    mock_post.return_value.status_code = HTTPStatus.OK

    upload_file = {"file": mock_file}
    upload_url = f"/extras/{instrument_folders[3]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file, headers=USER_HEADER)

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_fail_file_upload_to_non_existent_dir(mock_post, mock_file):
    """Tests if uploads to non existent instrument folders are rejected"""
    mock_post.return_value.status_code = HTTPStatus.OK

    upload_file = {"file": mock_file}
    upload_url = f"/extras/nonexistent-folder/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@patch("fia_api.core.auth.tokens.requests.post")
def test_fail_file_upload_to_non_extras(mock_post, mock_file):
    """Tests if uploads to folders not matching EXTRAS_DIRECTORY (base folder) are rejected"""
    mock_post.return_value.status_code = HTTPStatus.OK

    upload_file = {"file": mock_file}
    upload_url = f"/anUnexpectedFolder/{instrument_folders[6]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND
