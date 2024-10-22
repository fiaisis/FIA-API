from http import HTTPStatus

# from unittest.mock import Mock, patch
from starlette.testclient import TestClient

from fia_api.fia_api import app

client = TestClient(app)

# local_instrument_folders: list[str] = [
#     "alf",
#     "mari",
# ]

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

file_names: list[str] = ["test_file_1.txt", "test_file_2.png"]
files: dict[int, any] = {
    0: ("testfile.txt", b"Insert file content here", "text/plain"),
    1: ("testfile_2", b"Yet another file", "text/plain"),
}


def test_read_extras_populated():
    response = client.get("/extras")
    folders = response.json()

    assert response.status_code == HTTPStatus.OK
    assert folders == instrument_folders


def test_read_instrument_empty():
    response = client.get("/extras/alf")
    instrument_files = response.json()

    assert response.status_code == HTTPStatus.OK
    assert instrument_files == []


# def test_read_instrument_populated():
# run manual (redefined) upload with a fake folder /extras/inst
# then test to see if those files names are present here


def test_success_file_upload():
    file_id = 0
    upload_file = {"file": files[file_id]}
    upload_url = f"/extras/mari/{file_names[file_id]}"

    with TestClient(app) as client:
        response = client.post(upload_url, files=upload_file)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == f"Successfully uploaded {file_names[file_id]}"


def test_fail_file_upload_to_non_existent_dir():
    file_id = 0
    upload_file = {"file": files[file_id]}
    upload_url = f"/extras/nonexistent-folder/{file_names[file_id]}"

    with TestClient(app) as client:
        response = client.post(upload_url, files=upload_file)
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()["detail"].startswith("Invalid path being accessed")
        assert response.json()["detail"].rfind("No such file or directory") != -1


def test_fail_file_upload_to_non_extras():
    file_id = 1
    upload_file = {"file": files[file_id]}
    upload_url = f"/anUnexpectedFolder/mari{file_names[file_id]}"

    with TestClient(app) as client:
        response = client.post(upload_url, files=upload_file)
        assert response.status_code == HTTPStatus.NOT_FOUND
