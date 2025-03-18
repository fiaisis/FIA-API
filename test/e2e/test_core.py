"""end-to-end tests"""

import datetime
import os
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

import pytest
from db.data_models import Instrument, Job, JobOwner, JobType, Run, Script, State
from fastapi import HTTPException
from sqlalchemy.orm import make_transient
from starlette.testclient import TestClient

from fia_api.core.repositories import SESSION
from fia_api.core.responses import JobResponse
from fia_api.fia_api import app

from .constants import API_KEY_HEADER, STAFF_HEADER, USER_HEADER

client = TestClient(app)


TEST_JOB_OWNER = JobOwner(experiment_number=18204970)
TEST_INSTRUMENT = Instrument(instrument_name="NEWBIE", latest_run=1, specification={"foo": "bar"})
TEST_SCRIPT = Script(script="print('Script 1')", sha="some_sha", script_hash="some_hash")
TEST_JOB = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER,
    state=State.NOT_STARTED,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT,
    job_type=JobType.AUTOREDUCTION,
)
TEST_RUN = Run(
    filename="test_run",
    owner=TEST_JOB_OWNER,
    title="Test Run",
    users="User1, User2",
    run_start=datetime.datetime.now(datetime.UTC),
    run_end=datetime.datetime.now(datetime.UTC),
    good_frames=200,
    raw_frames=200,
    instrument=TEST_INSTRUMENT,
)
TEST_RUN.jobs.append(TEST_JOB)


@pytest.fixture()
def _user_owned_data_setup() -> None:
    """
    Set up the test database before module
    :return: None
    """
    with SESSION() as session:
        session.add(TEST_SCRIPT)
        session.add(TEST_INSTRUMENT)
        session.add(TEST_RUN)
        session.add(TEST_JOB)
        session.commit()
        session.refresh(TEST_SCRIPT)
        session.refresh(TEST_INSTRUMENT)
        session.refresh(TEST_RUN)
    yield
    with SESSION() as session:
        session.delete(TEST_RUN)
        session.delete(TEST_SCRIPT)
        session.delete(TEST_INSTRUMENT)
        session.delete(TEST_JOB)
        session.commit()
        session.flush()
        make_transient(TEST_RUN)
        make_transient(TEST_SCRIPT)
        make_transient(TEST_INSTRUMENT)
        make_transient(TEST_JOB)


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
    response = client.get("/jobs?limit=10", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    expected_number_of_jobs = 10
    assert len(response.json()) == expected_number_of_jobs


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_job_filtered_on_exact_experiment_number(mock_post):
    expected_experiment_number = 882000
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        '/jobs?include_run=true&filters={"experiment_number_in": [882000]}',
        headers=STAFF_HEADER,
    )
    data = response.json()
    assert len(data) == 1
    assert data[0]["run"]["experiment_number"] == expected_experiment_number


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_with_filters(mock_post):
    """Test count with filter"""
    expected_count = 4814
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get('/jobs/count?filters={"title":"n"}')
    assert response.json()["count"] == expected_count


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_by_instrument_with_filter(mock_post):
    """Test count by instrument with filter"""
    expected_count = 119
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get('/instrument/MARI/jobs/count?filters={"title":"n"}')
    assert response.json()["count"] == expected_count


@pytest.mark.parametrize("endpoint", ["/jobs", "/instrument/mari/jobs"])
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_with_filters(mock_post, endpoint):
    """Test get all jobs for staff with filters"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        f"{endpoint}?include_run=true&limit=5&filters={{"
        '"instrument_in":["MARI"],'
        '"job_state_in":["ERROR","SUCCESSFUL","UNSUCCESSFUL"],'
        '"title":"n",'
        '"experiment_number_after":115662,'
        '"experiment_number_before":923367,'
        '"filename":"MAR","job_start_before":"2023-02-05T00:00:00.000Z",'
        '"job_start_after":"2019-02-23T00:00:00.000Z",'
        '"job_end_before":"2022-03-23T00:00:00.000Z",'
        '"job_end_after":"2021-02-04T00:00:00.000Z",'
        '"run_start_before":"2022-02-17T00:00:00.000Z",'
        '"run_start_after":"2017-02-09T00:00:00.000Z",'
        '"run_end_before":"2022-02-04T00:00:00.000Z",'
        '"run_end_after":"2018-02-09T00:00:00.000Z"}',
        headers=STAFF_HEADER,
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()[0]
    assert 115661 < data["run"]["experiment_number"] < 923367  # noqa: PLR2004
    assert data["run"]["instrument_name"] == "MARI"
    assert data["state"] in ["ERROR", "SUCCESSFUL", "UNSUCCESSFUL"]
    assert "n" in data["run"]["title"].lower()
    assert data["run"]["filename"].startswith("/archive/NDXMAR")
    assert "2019-02-23T00:00:00.000Z" <= data["start"] <= "2023-02-05T00:00:00.000Z"
    assert "2021-02-04T00:00:00.000Z" <= data["end"] <= "2022-03-23T00:00:00.000Z"
    assert "2017-02-09T00:00:00.000Z" <= data["run"]["run_start"] <= "2022-02-17T00:00:00.000Z"
    assert "2018-02-09T00:00:00.000Z" <= data["run"]["run_end"] <= "2022-02-04T00:00:00.000Z"


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_job_for_staff_with_bad_filter_returns_400(mock_post):
    """Test get all jobs for staff with bad filter"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        '/jobs?limit=20&filters={"the game":["MARI"]}&include_run=True',
        headers=STAFF_HEADER,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_all_jobs_for_dev_mode():
    """Test get all jobs for staff"""
    with patch("fia_api.core.auth.tokens.DEV_MODE", True):
        response = client.get("/jobs?limit=10")
        assert response.status_code == HTTPStatus.OK
        expected_number_of_jobs = 10
        assert len(response.json()) == expected_number_of_jobs


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_job_for_user(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test get all jobs for staff"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs", headers=USER_HEADER)
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
    response = client.get("/jobs?include_run=true", headers=USER_HEADER)
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
    response = client.get("/job/5001", headers=STAFF_HEADER)
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
    response = client.get("/job/5001", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.scripts.acquisition.LOCAL_SCRIPT_DIR", "fia_api/local_scripts")
def test_get_prescript_when_job_does_not_exist():
    """
    Test return 404 when requesting pre script from non existant job
    :return:
    """
    response = client.get("/instrument/MARI/script?job_id=4324234")
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
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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
        response = client.get("/instrument/test/jobs", headers=STAFF_HEADER)
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
    response = client.get("/instrument/test/jobs", headers=STAFF_HEADER)
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
    response = client.get("/instrument/test/jobs", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_jobs_for_instrument_runs_included_for_staff(mock_post):
    """Test runs are included when requested for given instrument when instrument and jobs exist"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/test/jobs?include_run=true", headers=STAFF_HEADER)
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
    response = client.get("/instrument/foo/jobs", headers=STAFF_HEADER)
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
    response = client.get("/instrument/mari/jobs?limit=4", headers=STAFF_HEADER)
    assert len(response.json()) == 4  # noqa: PLR2004


@patch("fia_api.core.auth.tokens.requests.post")
def test_offset_jobs(mock_post):
    """Test results are offset"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/jobs", headers=STAFF_HEADER)
    response_two = client.get("/instrument/mari/jobs?offset=10", headers=STAFF_HEADER)
    assert response_one.json()[0] != response_two.json()[0]


@patch("fia_api.core.auth.tokens.requests.post")
def test_limit_offset_jobs(mock_post):
    """Test offset with limit"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response_one = client.get("/instrument/mari/jobs?limit=4", headers=STAFF_HEADER)
    response_two = client.get("/instrument/mari/jobs?limit=4&offset=10", headers=STAFF_HEADER)

    assert len(response_two.json()) == 4  # noqa: PLR2004
    assert response_one.json() != response_two.json()


def test_instrument_jobs_count():
    """Test instrument jobs count"""
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
    response = client.get("/instrument/het/specification", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "ask": 8893.939623321,
        "attorney": 4274,
        "become": 5873,
        "begin": 54.6477170013272,
        "decade": "dSKUxJgukcXlhktChZZh",
        "do": False,
        "purpose": False,
        "so": -8539.92322065455,
        "sure": 78316125067539.8,
        "system": 7065,
    }


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
    client.put("/instrument/tosca/specification", json={"foo": "bar"}, headers=STAFF_HEADER)
    response = client.get("/instrument/tosca/specification", headers=STAFF_HEADER)
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
    response = client.get("/jobs/runners", headers=USER_HEADER)
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


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_jobs_response_body_as_user_true_and_as_staff(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test that a single job is returned when a staff user gets all jobs with the as_user flag set to true"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs?as_user=true", headers=STAFF_HEADER)
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
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_all_jobs_as_user_false_and_as_staff(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test that multiple jobs are returned when a staff user gets all jobs with the as_user flag set to false"""
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiment_numbers_for_user_number.return_value = [1820497]
    response = client.get("/jobs?limit=10&as_user=false", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) > 1


@pytest.mark.usefixtures("_user_owned_data_setup")
@patch("fia_api.core.specifications.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mari_jobs_as_user_true_and_as_staff(mock_post, mock_get_experiment_numbers_for_user_number):
    """Test that a single job is returned when a staff user gets jobs from MARI with the as_user flag set to true"""
    mock_get_experiment_numbers_for_user_number.return_value = [18204970]
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/newbie/jobs?&as_user=true", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 1


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mari_jobs_as_user_false_and_as_staff(mock_post):
    """Test that multiple jobs are returned when a staff user gets jobs from MARI with the as_user flag set to false"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/mari/jobs?limit=10&as_user=false", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) > 1


@pytest.mark.usefixtures("_user_owned_data_setup")
def test_update_job_with_api_key():
    job = JobResponse.from_job(TEST_JOB)
    job.status_message = "hello"
    job.state = "SUCCESSFUL"
    response = client.patch("/job/5002", json=job.model_dump(mode="json"), headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.OK

    updated_response = response.json()
    assert updated_response["status_message"] == job.status_message
    assert updated_response["state"] == job.state
    assert updated_response["end"] == TEST_JOB.end
    assert updated_response["inputs"] == TEST_JOB.inputs
    assert updated_response["outputs"] == TEST_JOB.outputs
    assert updated_response["start"].replace("T", " ") == str(TEST_JOB.start)
    assert updated_response["runner_image"] == TEST_JOB.runner_image
    assert updated_response["type"] == str(TEST_JOB.job_type)


@pytest.mark.usefixtures("_user_owned_data_setup")
@patch("fia_api.core.auth.tokens.requests.post")
def test_update_job_as_staff(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    job = JobResponse.from_job(TEST_JOB)
    job.status_message = "hello"
    job.state = "SUCCESSFUL"
    response = client.patch("/job/5002", json=job.model_dump(mode="json"), headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK

    updated_response = response.json()
    assert updated_response["status_message"] == job.status_message
    assert updated_response["state"] == job.state
    assert updated_response["end"] == TEST_JOB.end
    assert updated_response["inputs"] == TEST_JOB.inputs
    assert updated_response["outputs"] == TEST_JOB.outputs
    assert updated_response["start"].replace("T", " ") == str(TEST_JOB.start)
    assert updated_response["runner_image"] == TEST_JOB.runner_image
    assert updated_response["type"] == str(TEST_JOB.job_type)


@pytest.mark.usefixtures("_user_owned_data_setup")
@patch("fia_api.core.auth.tokens.requests.post")
def test_update_job_fails_for_user(_):  # noqa: PT019
    response = client.patch("/job/1", json={"foo": "bar"}, headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_user_owned_data_setup")
def test_update_job_fails_with_no_auth():
    response = client.patch("/job/1", json={"foo": "bar"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_user_owned_data_setup")
def test_update_job_returns_404_when_id_doesn_t_exist():
    new_job = JobResponse.from_job(TEST_JOB)
    new_job.state = "SUCCESSFUL"
    response = client.patch("/job/-42069", headers=API_KEY_HEADER, json=new_job.model_dump(mode="json"))
    assert response.status_code == HTTPStatus.NOT_FOUND


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


TEST_JOB_ID = 5001
TEST_FILENAME = "output.txt"


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.utility.find_file_instrument")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_success(mock_get_job, mock_find_file):
    """Test that a valid request returns a file"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.return_value = {
        "id": TEST_JOB_ID,
        "owner": {"experiment_number": 12345},
        "instrument": {"instrument_name": "TEST"},
        "job_type": JobType.AUTOREDUCTION,
    }
    mock_find_file.return_value = f"MARI/RBNumber/RB20024/autoreduced/{TEST_FILENAME}"

    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.utility.find_file_instrument")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_not_found(mock_get_job, mock_find_file):
    """Test that a 404 is returned when file is not found"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.return_value = {
        "id": TEST_JOB_ID,
        "owner": {"experiment_number": 12345},
        "instrument": {"instrument_name": "TEST"},
        "job_type": JobType.AUTOREDUCTION,
    }
    mock_find_file.return_value = None

    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_find_file_unauthorized():
    """Test that a request without authentication returns 403"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_invalid_job(mock_get_job):
    """Test that a 404 is returned for an invalid job ID"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.side_effect = HTTPException(status_code=HTTPStatus.NOT_FOUND)

    response = client.get(f"/job/99999/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_no_owner(mock_get_job):
    """Test that an error is returned when job has no owner"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.return_value = {"id": TEST_JOB_ID, "owner": None}

    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Job has no owner." in response.text


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_experiment_number_missing(mock_get_job):
    """Test error when experiment number is missing but expected"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.return_value = {
        "id": TEST_JOB_ID,
        "owner": {"experiment_number": None},
        "instrument": {"instrument_name": "TEST"},
        "job_type": JobType.AUTOREDUCTION,
    }

    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Experiment number not found" in response.text


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_job_by_id")
def test_find_file_user_number_missing(mock_get_job):
    """Test error when user number is missing for SIMPLE jobs"""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_get_job.return_value = {
        "id": TEST_JOB_ID,
        "owner": {"experiment_number": None, "user_number": None},
        "instrument": {"instrument_name": "TEST"},
        "job_type": JobType.SIMPLE,
    }

    response = client.get(f"/job/{TEST_JOB_ID}/filename/{TEST_FILENAME}", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "User number not found" in response.text
