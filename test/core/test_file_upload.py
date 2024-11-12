import os
import random
from http import HTTPStatus
from pathlib import Path
import shutil
from importlib import reload
import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def mock_file():
    file_names: list[str] = ["test_file_1.txt", "test_file_2.png"]
    files: dict[int, any] = {
        0: (file_names[0], b"Insert file content here", "text/plain"),
        1: (file_names[1], b"Yet another file", "text/plain"),
    }

    return files[random.randint(0, 1)]  # noqa: S311


@pytest.fixture
def client(permissive_tmp_path, monkeypatch, autouse=True):
    # tmp_path = tmp_path_factory.mktemp("mock-extras", numbered=True)
    # APILOG: THE ROOT DIRECTORY IS: /tmp/pytest-of-tuz58699/pytest-16/test_read_extras_empty0
    # IT NEVER UPDATES
    # os.environ["EXTRAS_DIRECTORY"] = str(permissive_tmp_path)
    monkeypatch.setenv("EXTRAS_DIRECTORY", str(permissive_tmp_path))
    from fia_api.fia_api import app

    yield TestClient(app=app)
    if "EXTRAS_DIRECTORY" in os.environ:
        del os.environ["EXTRAS_DIRECTORY"]


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


# @pytest.fixture(autouse=True)
# def test_temp_directory_is_empty():
#     # Assert that the temporary directory is empty
#     assert not any(str(os.environ["EXTRAS_DIRECTORY"]).iterdir()), "Temporary directory is not clean!"

#     # # Write something to ensure it's usable
#     # temp_file = tmp_path / "tempfile.txt"
#     # temp_file.write_text("Checking isolation!")
#     # assert temp_file.read_text() == "Checking isolation!"


@pytest.fixture
def permissive_tmp_path(tmp_path):
    tmp_path.chmod(0o775)
    tmp_path.parent.chmod(0o775)
    return tmp_path


def test_read_extras_populated(client):
    """Tests the root folders is populated (instrument folders exist)"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_read_extras_populated is: ", root_folder)

    print("it contains", os.listdir(root_folder))
    for folder in sorted(instrument_folders):
        Path(root_folder / folder).mkdir(parents=True, exist_ok=True)

    response = client.get("/extras")
    print("post test pre assert contains", os.listdir(root_folder))
    # print(response.json())
    # print(instrument_folders)
    assert True == False
    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == instrument_folders


def test_read_extras_empty(client):
    """Tests the root folder is empty"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("root folder in test_read_extras_empty ", root_folder)
    response = client.get("/extras")
    folders = response.json()
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("root folder is in extras empty", root_folder)

    # '/tmp/pytest-...0/mock-extras
    # assert os.environ["EXTRAS_DIRECTORY"] == "temp dir keep track"

    # assert os.listdir(Path(os.environ["EXTRAS_DIRECTORY"])) == "This is the actual folders"
    assert True == False
    assert folders == []
    assert response.status_code == HTTPStatus.OK


def test_read_instrument_empty(client):
    """Tests that a randomly selected instrument folder is empty"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_read_instrument_empty is: ", root_folder)
    response = client.get(f"/extras/{instrument_folders[0]}")
    instrument_files = response.json()
    assert True == False
    assert response.status_code == HTTPStatus.OK
    assert instrument_files == []


def test_read_instrument_populated(client):
    """Tests if files under instrument folder are read correctly"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_read_instrument_populated is: ", root_folder)
    # Insert two files (creating directories and files)
    file_directory = Path(root_folder / instrument_folders[2]) / "filename1"
    file_directory2 = Path(root_folder / instrument_folders[2]) / "filename2"
    file_directory.mkdir(parents=True, exist_ok=True)
    Path.touch(file_directory)
    Path.touch(file_directory2)
    # check contents of the instrument folder
    response = client.get(f"/extras/{instrument_folders[2]}")
    assert True == False

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json()) == sorted([str(file_directory), str(file_directory2)])


def test_success_file_upload(client, mock_file):
    """Tests if files are uploaded successfully"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_success_file_upload is: ", root_folder)
    upload_file = {"file": mock_file}
    upload_url = f"/extras/{instrument_folders[3]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)
    assert True == False

    assert response.status_code == HTTPStatus.OK
    assert response.json() == f"Successfully uploaded {mock_file[0]}"


def test_fail_file_upload_to_non_existent_dir(client, mock_file):
    """Tests if uploads to non existent instrument folders are rejected"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_fail_file_upload_to_non_existent_dir is: ", root_folder)
    upload_file = {"file": mock_file}
    upload_url = f"/extras/nonexistent-folder/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)
    assert True == False

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"].startswith("Invalid path being accessed")
    assert response.json()["detail"].rfind("No such file or directory") != -1


def test_fail_file_upload_to_non_extras(client, mock_file):
    """Tests if uploads to folders not matching EXTRAS_DIRECTORY (base folder) are rejected"""
    root_folder = Path(os.environ["EXTRAS_DIRECTORY"])
    print("\n root folder in test_fail_file_upload_to_non_extras is: ", root_folder)
    upload_file = {"file": mock_file}
    upload_url = f"/anUnexpectedFolder/{instrument_folders[6]}/{mock_file[0]}"
    response = client.post(upload_url, files=upload_file)
    assert True == False

    assert response.status_code == HTTPStatus.NOT_FOUND
