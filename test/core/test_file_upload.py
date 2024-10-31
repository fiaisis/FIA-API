import os
import random
from http import HTTPStatus
from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def mock_file():
    file_names: list[str] = ["test_file_1.txt", "test_file_2.png"]
    files: dict[int, any] = {
        0: (file_names[0], b"Insert file content here", "text/plain"),
        1: (file_names[1], b"Yet another file", "text/plain"),
    }

    return files[random.randint(0, 1)]  # noqa: S311


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("mock-extras", numbered=False)
    os.environ["EXTRAS_DIRECTORY"] = str(tmp_path)

    # import app only after setting the env var
    from fia_api.fia_api import app

    return TestClient(app)


instrument_folders: list[str] = [
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


def test_read_extras_empty(client):
    """Tests the root folder is empty"""
    response = client.get("/extras")
    folders = response.json()

    assert folders == []
    assert response.status_code == HTTPStatus.OK


def test_read_extras_populated(client):
    """Tests the root folders is populated (instrument folders exist)"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    for folder in sorted(instrument_folders):
        Path(root_folder / folder).mkdir()
    response = client.get("/extras")

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == instrument_folders


def test_read_instrument_empty(client):
    """Tests that a randomly selected instrument folder is empty"""
    response = client.get(f"/extras/{instrument_folders[0]}")
    instrument_files = response.json()

    assert response.status_code == HTTPStatus.OK
    assert instrument_files == []


def test_read_instrument_populated(client):
    """Tests if files under instrument folder are read correctly"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    # Insert two files (creating directories and files)
    file_directory = Path(root_folder / instrument_folders[2]) / "filename1"
    file_directory2 = Path(root_folder / instrument_folders[2]) / "filename2"
    file_directory.mkdir(parents=True, exist_ok=True)
    Path.touch(file_directory)
    Path.touch(file_directory2)
    # check contents of the instrument folder
    response = client.get(f"/extras/{instrument_folders[2]}")

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == sorted([str(file_directory), str(file_directory2)])


def test_success_file_upload(client, mock_file):
    """Tests if files are uploaded successfully"""
    upload_file = {"file": mock_file}
    upload_url = f"/extras/{instrument_folders[3]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == f"Successfully uploaded {mock_file[0]}"


def test_fail_file_upload_to_non_existent_dir(client, mock_file):
    """Tests if uploads to non existent instrument folders are rejected"""
    upload_file = {"file": mock_file}
    upload_url = f"/extras/nonexistent-folder/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"].startswith("Invalid path being accessed")
    assert response.json()["detail"].rfind("No such file or directory") != -1


def test_fail_file_upload_to_non_extras(client, mock_file):
    """Tests if uploads to folders not matching EXTRAS_DIRECTORY (base folder) are rejected"""
    upload_file = {"file": mock_file}
    upload_url = f"/anUnexpectedFolder/{instrument_folders[6]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)

    assert response.status_code == HTTPStatus.NOT_FOUND
