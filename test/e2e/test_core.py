"""
end-to-end tests
"""

import os
from http import HTTPStatus
from unittest import mock
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.fia_api import app
from test.utils import FIA_FAKER_PROVIDER

client = TestClient(app)
os.environ["FIA_API_API_KEY"] = str(mock.MagicMock())

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


def test_get_job_by_id_no_token_results_in_http_forbidden():
    """
    Test 404 for job not existing
    :return:
    """
    response = client.get("/job/123144324234234234")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_job_for_staff(mock_post):
    """Test get all jobs for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/jobs?limit=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 10
    assert len(response.json()) == expected_number_of_jobs


def test_get_all_jobs_for_dev_mode():
    """Test get all jobs for staff"""
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/jobs?limit=10")
        assert response.status_code == HTTPStatus.OK
        expected_number_of_jobs = 10
        assert len(response.json()) == expected_number_of_jobs


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_as_user(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all jobs with as_user flag for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs?as_user=true", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 5001,
            "end": None,
            "inputs": {
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
            "outputs": None,
            "start": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "script": None,
            "stacktrace": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]


@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_jobs_as_user_dev_mode(mock_get_experiment_numbers_for_user_number):
    """Test get all jobs with as_user flag in dev mode"""
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/jobs?as_user=true")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == [
            {
                "id": 5001,
                "end": None,
                "inputs": {
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
                "outputs": None,
                "start": None,
                "state": "NOT_STARTED",
                "status_message": None,
                "script": None,
                "stacktrace": None,
                "runner_image": None,
                "type": "JobType.AUTOREDUCTION",
            }
        ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_as_user_false_for_staff(mock_post):
    """Test get all jobs with as_user flag set to false"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/jobs?as_user=false&limit=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 10
    assert len(response.json()) == expected_number_of_jobs


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_job_for_user(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all jobs for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 1
    assert len(response.json()) == expected_number_of_jobs
    assert response.json() == [
        {
            "id": 5001,
            "end": None,
            "inputs": {
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
            "outputs": None,
            "start": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "script": None,
            "stacktrace": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_job_for_user_include_run(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all jobs for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs?include_run=true", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 1
    assert len(response.json()) == expected_number_of_jobs
    assert response.json() == [
        {
            "id": 5001,
            "end": None,
            "run": {
                "experiment_number": 1820497,
                "filename": "MAR25581.nxs",
                "good_frames": 6452,
                "instrument_name": "TEST",
                "raw_frames": 8067,
                "run_end": "2019-03-22T10:18:26",
                "run_start": "2019-03-22T10:15:44",
                "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
                "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
            },
            "inputs": {
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
            "outputs": None,
            "start": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "script": None,
            "stacktrace": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_job_by_id_job_exists_for_staff(mock_post):
    """
    Test job returned for id that exists
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/job/5001", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 5001,
        "end": None,
        "inputs": {
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
        "outputs": None,
        "start": None,
        "state": "NOT_STARTED",
        "status_message": None,
        "run": {
            "experiment_number": 1820497,
            "filename": "MAR25581.nxs",
            "good_frames": 6452,
            "instrument_name": "TEST",
            "raw_frames": 8067,
            "run_end": "2019-03-22T10:18:26",
            "run_start": "2019-03-22T10:15:44",
            "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
            "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
        },
        "script": None,
        "stacktrace": None,
        "runner_image": None,
        "type": "JobType.AUTOREDUCTION",
    }


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_job_by_id_job_exists_for_user_no_perms(mock_post):
    """
    Test Forbidden returned for user lacking permissions
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/job/5001", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.scripts.acquisition.LOCAL_SCRIPT_DIR", "fia_api/local_scripts")
def test_get_prescript_when_job_does_not_exist():
    """
    Test return 404 when requesting pre script from non existant job
    :return:
    """
    response = client.get("/instrument/mari/script?job_id=4324234")
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
def test_get_test_prescript_for_job():
    """
    Test the return of transformed test script
    :return: None
    """
    response = client.get("/instrument/test/script?job_id=1")
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


def test_get_jobs_for_instrument_no_token_results_in_forbidden():
    """
    Test result with no token is forbidden
    :return: None
    """
    response = client.get("/instrument/test/jobs")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_jobs_for_instrument_jobs_exist_for_dev_mode():
    """
    Test array of jobs returned for given instrument when the instrument and jobs exist
    :return: None
    """
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/instrument/test/jobs", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
        assert response.status_code == HTTPStatus.OK
        assert response.json() == [
            {
                "id": 5001,
                "end": None,
                "inputs": {
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
                "outputs": None,
                "start": None,
                "state": "NOT_STARTED",
                "status_message": None,
                "script": None,
                "stacktrace": None,
                "runner_image": None,
                "type": "JobType.AUTOREDUCTION",
            }
        ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_for_instrument_jobs_exist_for_staff(mock_post):
    """
    Test array of jobs returned for given instrument when the instrument and jobs exist
    :return: None
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/jobs", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 5001,
            "end": None,
            "inputs": {
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
            "outputs": None,
            "start": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "script": None,
            "stacktrace": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.auth.experiments.requests.get")
def test_get_jobs_for_instrument_jobs_dont_exist_for_user(mock_get, mock_post):
    """
    Test empty array of jobs returned for given instrument when the instrument and jobs exist
    :return: None
    """
    mock_get.return_value.status_code = HTTPStatus.OK
    mock_get.return_value.json.return_value = []
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/jobs", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_for_instrument_runs_included_for_staff(mock_post):
    """Test runs are included when requested for given instrument when instrument and jobs exist"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/jobs?include_run=true", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 5001,
            "end": None,
            "inputs": {
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
            "outputs": None,
            "start": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "run": {
                "experiment_number": 1820497,
                "filename": "MAR25581.nxs",
                "good_frames": 6452,
                "instrument_name": "TEST",
                "raw_frames": 8067,
                "run_end": "2019-03-22T10:18:26",
                "run_start": "2019-03-22T10:15:44",
                "title": "Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
                "users": "Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
            },
            "script": None,
            "stacktrace": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]


@patch("fia_api.core.auth.tokens.requests.post")
def test_jobs_by_instrument_no_jobs(mock_post):
    """
    Test empty array returned when no jobs for instrument
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/foo/jobs", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


def test_jobs_count():
    """
    Test count endpoint for all jobs
    :return:
    """
    response = client.get("/jobs/count")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["count"] == 5001  # noqa: PLR2004


@patch("fia_api.core.auth.tokens.requests.post")
def test_limit_jobs(mock_post):
    """Test jobs can be limited"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/mari/jobs?limit=4", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert len(response.json()) == 4  # noqa: PLR2004


@patch("fia_api.core.auth.tokens.requests.post")
def test_offset_jobs(mock_post):
    """
    Test results are offset
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/jobs", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    response_two = client.get("/instrument/mari/jobs?offset=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response_one.json()[0] != response_two.json()[0]


@patch("fia_api.core.auth.tokens.requests.post")
def test_limit_offset_jobs(mock_post):
    """
    Test offset with limit
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/jobs?limit=4", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    response_two = client.get(
        "/instrument/mari/jobs?limit=4&offset=10", headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )

    assert len(response_two.json()) == 4  # noqa: PLR2004
    assert response_one.json() != response_two.json()


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_jobs_as_user_false_for_staff(mock_post):
    """Test get MARI jobs with as_user flag set to false"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        "/instrument/mari/jobs?limit=10&as_user=false", headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 10
    assert len(response.json()) == expected_number_of_jobs


@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_instrument_jobs_as_user_dev_mode(mock_get_experiment_numbers_for_user_number):
    """Test get MARI jobs with as_user flag in dev mode"""
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/instrument/mari/jobs?as_user=true&limit=1")
        assert response.status_code == HTTPStatus.OK
        expected_number_of_jobs = 1
        assert len(response.json()) == expected_number_of_jobs


def test_instrument_jobs_count():
    """
    Test instrument jobs count
    """
    response = client.get("/instrument/TEST/jobs/count")
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


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_specification(mock_post):
    """
    Test correct spec for instrument returned
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/het/specification", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"stop": False}


def test_get_instrument_specification_no_jwt_returns_403():
    """
    Test correct spec for instrument returned
    :return:
    """

    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_instrument_specification_bad_jwt():
    """
    Test correct spec for instrument returned
    :return:
    """
    response = client.get("/instrument/het/specification", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_specification(mock_post):
    """Test instrument put is updated"""
    mock_post.return_value.status_code = HTTPStatus.OK
    client.put(
        "/instrument/tosca/specification", json={"foo": "bar"}, headers={"Authorization": f"Bearer {STAFF_TOKEN}"}
    )
    response = client.get("/instrument/tosca/specification", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"foo": "bar"}


def test_put_instrument_specification_no_api_key():
    """Test instrument put is updated"""
    client.put("/instrument/het/specification", json={"foo": "bar"})
    response = client.get("/instrument/het/specification")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners(mock_post):
    """Test endpoint contains all the Mantid runners."""
    mock_post.return_value.status_code = HTTPStatus.OK
    expected_runners = ["6.8.0", "6.9.0", "6.9.1", "6.10.0", "6.11.0"]
    response = client.get("/jobs/runners", headers={"Authorization": f"Bearer {USER_TOKEN}"})
    assert response.status_code == HTTPStatus.OK
    for runner in expected_runners:
        assert runner in response.json()


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners_no_api_key(mock_post):
    """Test endpoint returns forbidden if no API key supplied."""
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/jobs/runners")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners_bad_jwt(mock_post):
    """Test endpoint returns forbidden if bad JWT supplied."""
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/jobs/runners", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_all_jobs")
def test_get_jobs_as_user_flag_for_staff(mock_post, mock_get_all_jobs):
    """Test get all jobs with as_user flag set to true and false for a staff user"""
    mock_get_all_jobs.return_value = [
        {
            "id": 1234,
            "state": "COMPLETED",
            "inputs": {},
            "outputs": None,
            "start": None,
            "end": None,
            "type": "JobType.AUTOREDUCTION",
        },
        {
            "id": 5678,
            "state": "FAILED",
            "inputs": {},
            "outputs": None,
            "start": None,
            "end": None,
            "type": "JobType.AUTOREDUCTION",
        },
    ]

    mock_post.return_value.status_code = (
        HTTPStatus.OK
    )  # mock_get_experiment_numbers_for_user_number.return_value = [1820497]

    response_as_user = client.get("/jobs?as_user=true", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response_as_user.status_code == HTTPStatus.OK

    response_not_as_user = client.get("/jobs?as_user=false", headers={"Authorization": f"Bearer {STAFF_TOKEN}"})
    assert response_not_as_user.status_code == HTTPStatus.OK

    assert len(response_as_user.json()) == len(response_not_as_user.json())
