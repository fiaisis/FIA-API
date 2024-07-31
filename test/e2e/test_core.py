"""
end-to-end tests
"""

from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.fia_api import app
from test.utils import FIA_FAKER_PROVIDER

client = TestClient(app)

faker = FIA_FAKER_PROVIDER

USER_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # noqa: S105
    ".eyJ1c2VybnVtYmVyIjoxMjM0LCJyb2xlIjoidXNlciIsInVzZXJuYW1lIjoiZm9vIiwiZXhwIjo0ODcyNDY4MjYzfQ."
    "99rVB56Y6-_rJikqlZQia6koEJJcpY0T_QV-fZ43Mok"
)
STAFF_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."  # noqa: S105
    "eyJ1c2VybnVtYmVyIjoxMjM0LCJyb2xlIjoic3RhZmYiLCJ1c2VybmFtZSI6ImZvbyIsImV4cCI6NDg3MjQ2ODk4M30."
    "-ktYEwdUfg5_PmUocmrAonZ6lwPJdcMoklWnVME1wLE"
)


def test_get_reduction_by_id_no_token_results_in_http_forbidden():
    """
    Test 404 for reduction not existing
    :return:
    """
    response = client.get("/reduction/123144324234234234")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_reduction_for_staff(mock_post):
    """Test get all reductions for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/reductions?limit=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_reductions = 10
    assert len(response.json()) == expected_number_of_reductions


def test_get_all_reductions_for_dev_mode():
    """Test get all reductions for staff"""
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/reductions?limit=10")
        assert response.status_code == HTTPStatus.OK
        expected_number_of_reductions = 10
        assert len(response.json()) == expected_number_of_reductions


@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_reduction_for_user(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all reductions for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/reductions", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_reductions = 1
    assert len(response.json()) == expected_number_of_reductions
    assert response.json() == [
        {
            "id": 5001,
            "reduction_end": None,
            "reduction_inputs": {
                "ei": "'auto'",
                "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
                "monovan": 0,
                "remove_bkg": True,
                "runno": 25581,
                "sam_mass": 0.0,
                "sam_rmm": 0.0,
                "sum_runs": False,
                "wbvan": 12345,
            },
            "reduction_outputs": None,
            "reduction_start": None,
            "reduction_state": "NOT_STARTED",
            "reduction_status_message": None,
            "script": None,
            "stacktrace": None,
        }
    ]


@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_reduction_for_user_include_run(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all reductions for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/reductions?include_runs=true", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_reductions = 1
    assert len(response.json()) == expected_number_of_reductions
    assert response.json() == [
        {
            "id": 5001,
            "reduction_end": None,
            "runs": [
                {
                    "experiment_number": 1820497,
                    "filename": "MAR25581.nxs",
                    "good_frames": 6452,
                    "instrument_name": "TEST",
                    "raw_frames": 8067,
                    "run_end": "2019-03-22T10:18:26",
                    "run_start": "2019-03-22T10:15:44",
                    "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT " "on not on all LAB",
                    "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
                }
            ],
            "reduction_inputs": {
                "ei": "'auto'",
                "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
                "monovan": 0,
                "remove_bkg": True,
                "runno": 25581,
                "sam_mass": 0.0,
                "sam_rmm": 0.0,
                "sum_runs": False,
                "wbvan": 12345,
            },
            "reduction_outputs": None,
            "reduction_start": None,
            "reduction_state": "NOT_STARTED",
            "reduction_status_message": None,
            "script": None,
            "stacktrace": None,
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_reduction_by_id_reduction_exists_for_staff(mock_post):
    """
    Test reduction returned for id that exists
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/reduction/5001", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 5001,
        "reduction_end": None,
        "reduction_inputs": {
            "ei": "'auto'",
            "sam_mass": 0.0,
            "sam_rmm": 0.0,
            "monovan": 0,
            "remove_bkg": True,
            "sum_runs": False,
            "runno": 25581,
            "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/"
            "964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
            "wbvan": 12345,
        },
        "reduction_outputs": None,
        "reduction_start": None,
        "reduction_state": "NOT_STARTED",
        "reduction_status_message": None,
        "runs": [
            {
                "experiment_number": 1820497,
                "filename": "MAR25581.nxs",
                "good_frames": 6452,
                "instrument_name": "TEST",
                "raw_frames": 8067,
                "run_end": "2019-03-22T10:18:26",
                "run_start": "2019-03-22T10:15:44",
                "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
                "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
            }
        ],
        "script": None,
        "stacktrace": None,
    }


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_reduction_by_id_reduction_exists_for_user_no_perms(mock_post):
    """
    Test Forbidden returned for user lacking permissions
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/reduction/5001", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.scripts.acquisition.LOCAL_SCRIPT_DIR", "fia_api/local_scripts")
def test_get_prescript_when_reduction_does_not_exist():
    """
    Test return 404 when requesting pre script from non existant reduction
    :return:
    """
    response = client.get("/instrument/mari/script?reduction_id=4324234")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


@patch("fia_api.scripts.acquisition._get_script_from_remote")
def test_unsafe_path_request_returns_400_status(mock_get_from_remote):
    """
    Test that a 400 is returned for unsafe characters in script request
    :return:
    """
    mock_get_from_remote.side_effect = RuntimeError
    response = client.get("/instrument/mari./script")  # %2F is encoded /
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"message": "The given request contains bad characters"}


@patch("fia_api.scripts.acquisition.LOCAL_SCRIPT_DIR", "fia_api/local_scripts")
def test_get_test_prescript_for_reduction():
    """
    Test the return of transformed test script
    :return: None
    """
    response = client.get("/instrument/test/script?reduction_id=1")
    assert response.status_code == HTTPStatus.OK
    response_object = response.json()

    assert response_object["is_latest"]
    assert (
        response_object["value"]
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


def test_get_reductions_for_instrument_no_token_results_in_forbidden():
    """
    Test result with no token is forbidden
    :return: None
    """
    response = client.get("/instrument/test/reductions")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_reductions_for_instrument_reductions_exist_for_dev_mode():
    """
    Test array of reductions returned for given instrument when the instrument and reductions exist
    :return: None
    """
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/instrument/test/reductions", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
        assert response.status_code == HTTPStatus.OK
        assert response.json() == [
            {
                "id": 5001,
                "reduction_end": None,
                "reduction_inputs": {
                    "ei": "'auto'",
                    "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/"
                    "964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
                    "monovan": 0,
                    "remove_bkg": True,
                    "runno": 25581,
                    "sam_mass": 0.0,
                    "sam_rmm": 0.0,
                    "sum_runs": False,
                    "wbvan": 12345,
                },
                "reduction_outputs": None,
                "reduction_start": None,
                "reduction_state": "NOT_STARTED",
                "reduction_status_message": None,
                "script": None,
                "stacktrace": None,
            }
        ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_reductions_for_instrument_reductions_exist_for_staff(mock_post):
    """
    Test array of reductions returned for given instrument when the instrument and reductions exist
    :return: None
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/reductions", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 5001,
            "reduction_end": None,
            "reduction_inputs": {
                "ei": "'auto'",
                "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/"
                "964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
                "monovan": 0,
                "remove_bkg": True,
                "runno": 25581,
                "sam_mass": 0.0,
                "sam_rmm": 0.0,
                "sum_runs": False,
                "wbvan": 12345,
            },
            "reduction_outputs": None,
            "reduction_start": None,
            "reduction_state": "NOT_STARTED",
            "reduction_status_message": None,
            "script": None,
            "stacktrace": None,
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.auth.experiments.requests.get")
def test_get_reductions_for_instrument_reductions_exist_for_user(mock_get, mock_post):
    """
    Test empty array of reductions returned for given instrument when the instrument and reductions exist
    :return: None
    """
    mock_get.return_value.status_code = HTTPStatus.OK
    mock_get.return_value.json.return_value = []
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/reductions", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_reductions_for_instrument_runs_included_for_staff(mock_post):
    """Test runs are included when requested for given instrument when instrument and reductions exist"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        "/instrument/test/reductions?include_runs=true", headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 5001,
            "reduction_end": None,
            "reduction_inputs": {
                "ei": "'auto'",
                "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
                "monovan": 0,
                "remove_bkg": True,
                "runno": 25581,
                "sam_mass": 0.0,
                "sam_rmm": 0.0,
                "sum_runs": False,
                "wbvan": 12345,
            },
            "reduction_outputs": None,
            "reduction_start": None,
            "reduction_state": "NOT_STARTED",
            "reduction_status_message": None,
            "runs": [
                {
                    "experiment_number": 1820497,
                    "filename": "MAR25581.nxs",
                    "good_frames": 6452,
                    "instrument_name": "TEST",
                    "raw_frames": 8067,
                    "run_end": "2019-03-22T10:18:26",
                    "run_start": "2019-03-22T10:15:44",
                    "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT " "on not on all LAB",
                    "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
                }
            ],
            "script": None,
            "stacktrace": None,
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_reductions_by_instrument_no_reductions(mock_post):
    """
    Test empty array returned when no reductions for instrument
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/foo/reductions", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


def test_reductions_count():
    """
    Test count endpoint for all reductions
    :return:
    """
    response = client.get("/reductions/count")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["count"] == 5001  # noqa: PLR2004


@patch("fia_api.core.auth.tokens.requests.post")
def test_limit_reductions(mock_post):
    """Test reductions can be limited"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/mari/reductions?limit=4", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert len(response.json()) == 4  # noqa: PLR2004


@patch("fia_api.core.auth.tokens.requests.post")
def test_offset_reductions(mock_post):
    """
    Test results are offset
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/reductions", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    response_two = client.get(
        "/instrument/mari/reductions?offset=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )
    assert response_one.json()[0] != response_two.json()[0]


@patch("fia_api.core.auth.tokens.requests.post")
def test_limit_offset_reductions(mock_post):
    """
    Test offset with limit
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/reductions?limit=4", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    response_two = client.get(
        "/instrument/mari/reductions?limit=4&offset=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )

    assert len(response_two.json()) == 4  # noqa: PLR2004
    assert response_one.json() != response_two.json()


def test_instrument_reductions_count():
    """
    Test instrument reductions count
    """
    response = client.get("/instrument/TEST/reductions/count")
    assert response.json()["count"] == 1


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


def test_get_instrument_specification():
    """
    Test correct spec for instrument returned
    :return:
    """

    response = client.get("/instrument/het/specification", headers={"Authorization": "Bearer shh"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"stop": False}


def test_get_instrument_specification_no_api_key_returns_403():
    """
    Test correct spec for instrument returned
    :return:
    """

    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_instrument_specification_bad_api_key_returns_403():
    """
    Test correct spec for instrument returned
    :return:
    """

    response = client.get("/instrument/het/specification", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get("/instrument/het/specification", headers={"Authorization": "Bearer foo"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_put_instrument_specification():
    """Test instrument put is updated"""
    client.put("/instrument/tosca/specification", json={"foo": "bar"}, headers={"Authorization": "Bearer shh"})
    response = client.get("/instrument/tosca/specification", headers={"Authorization": "Bearer shh"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"foo": "bar"}


def test_put_instrument_specification_no_api_key():
    """Test instrument put is updated"""
    client.put("/instrument/het/specification", json={"foo": "bar"})
    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.FORBIDDEN
