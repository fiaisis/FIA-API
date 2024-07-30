"""
end 2 end test cases for script acquisition
"""

# pylint: disable=line-too-long, wrong-import-order
import re
from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.fia_api import app

client = TestClient(app)


def assert_is_commit_sha(string: str) -> None:
    """
    assert given string is a commit sha
    :param string: the string to check
    :return: None
    """
    assert re.match("^[a-f0-9]{7,40}$", string) is not None


@patch("fia_api.scripts.acquisition.LOCAL_SCRIPT_DIR", "fia_api/local_scripts")
def test_get_default_test_prescript():
    """
    Test obtaining of untransformed mari pre script
    :return: None
    """
    response = client.get("/instrument/test/script")

    assert response.status_code == HTTPStatus.OK
    response_object = response.json()
    assert response_object["is_latest"]
    assert (
        response_object["value"]
        == """from __future__ import print_function

print("Doing some science")

x = 4
y = 2

for i in range(20):
    x *= y

def something() -> None:
    return

something()
"""
    )
    assert_is_commit_sha(response_object["sha"])


def test_get_script_by_sha_no_reduction_id_instrument_exists_hash_exists():
    """
    Test script returned by hash untransformed
    :return: None
    """
    response = client.get("/instrument/test/script/sha/64c6121")
    assert response.json() == {
        "is_latest": False,
        "sha": "64c6121",
        "value": "from __future__ import print_function\n"
        "\n"
        'print("Doing some science")\n'
        "\n"
        "x = 4\n"
        "y = 2\n"
        "\n"
        "for i in range(20):\n"
        "    x *= y\n"
        "\n"
        "def something() -> None:\n"
        "    return\n"
        "\n"
        "something()\n",
    }


def test_get_script_by_sha_instrument_doesnt_exist_returns_404():
    """
    Test 404 response when instrument doesnt exist
    :return: None
    """
    response = client.get("/instrument/foo/script/sha/64c6121")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


def test_get_script_by_sha_instrument_exists_sha_doesnt_exist_returns_404():
    """
    Test 404 when hash does not exist
    :return: None
    """
    response = client.get("/instrument/test/script/sha/12345")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


def test_get_script_by_sha_instrument_and_sha_doesnt_exist_returns_404():
    """
    Test 404 when neither hash nor instrument exist
    :return: None
    """
    response = client.get("/instrument/foo/script/sha/12345")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


def test_get_script_by_sha_with_job_id():
    """
    Test transformed script can be returned from hash when job id is provided
    :return: None
    """
    response = client.get("/instrument/test/script/sha/64c6121?job_id=1")
    assert response.status_code == HTTPStatus.OK
    response = response.json()
    assert response["is_latest"] is False
    assert response["sha"] == "64c6121"
    assert (
        response["value"]
        == """from __future__ import print_function
from mantid.kernel import ConfigService
ConfigService.Instance()[\"network.github.api_token\"] = \"\"
# This line is inserted via test


x = 22
y = 2

for i in range(20):
    x *= y

def something() -> None:
    return

something()"""
    )


def test_get_default_prescript_instrument_does_not_exist():
    """
    Test 404 for requesting script from unknown instrument
    :return:
    """
    response = client.get("/instrument/foo/script")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "message": "The script could not be found locally or on remote, it is likely the script does not exist"
    }
