"""end-to-end tests"""

import datetime
import io
import os
import zipfile
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import make_transient
from starlette.testclient import TestClient

from fia_api.core.models import Instrument, Job, JobOwner, JobType, Run, Script, State
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


@pytest.fixture
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
    expected_experiment_number = 818853
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        '/jobs?include_run=true&filters={"experiment_number_in": [818853]}',
        headers=STAFF_HEADER,
    )
    data = response.json()
    assert len(data) == 1
    assert data[0]["run"]["experiment_number"] == expected_experiment_number


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_with_filters(mock_post):
    """Test count with filter"""
    expected_count = 4813
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get('/jobs/count?filters={"title":"n"}')
    assert response.json()["count"] == expected_count


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_by_instrument_with_filter(mock_post):
    """Test count by instrument with filter"""
    expected_count = 118
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
        "and": "azwVvzwemQhTlFQDUuXm",
        "animal": 2098,
        "area": True,
        "commercial": False,
        "dinner": True,
        "environmental": False,
        "exactly": False,
        "green": -3060079982.5833,
        "maybe": 4116,
        "might": True,
        "sea": "hOJYuVxrfTPqxqbctkBj",
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
def test_get_instrument_latest_run(mock_post):
    """
    Test correct latest run for instrument returned
    :return:
    """
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/let/latest-run", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"latest_run": "75827"}


def test_get_instrument_latest_run_no_jwt_returns_403():
    """
    Test that getting latest run without JWT returns 403
    :return:
    """
    response = client.get("/instrument/het/latest-run")
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_instrument_latest_run_user_token_returns_403(mock_post):
    """Test that getting latest run with non staff token returns 403"""
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/instrument/het/latest-run", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_latest_run_with_user_token_returns_403(mock_post):
    mock_post.return_value.status_code = HTTPStatus.OK
    """Test that putting latest run with non staff token returns 403"""
    response = client.put("/instrument/het/latest-run", json={"latest_run": "75827"}, headers=USER_HEADER)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_instrument_latest_run_bad_jwt():
    """
    Test that getting latest run with bad JWT returns 403
    :return:
    """
    response = client.get("/instrument/het/latest-run", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_put_instrument_latest_run(mock_post):
    """Test instrument latest run is updated"""
    mock_post.return_value.status_code = HTTPStatus.OK
    client.put("/instrument/tosca/latest-run", json={"latest_run": "54321"}, headers=STAFF_HEADER)
    response = client.get("/instrument/tosca/latest-run", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"latest_run": "54321"}


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
    response = client.patch(f"/job/{TEST_JOB.id}", json=job.model_dump(mode="json"), headers=API_KEY_HEADER)
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
    response = client.patch(f"/job/{TEST_JOB.id}", json=job.model_dump(mode="json"), headers=STAFF_HEADER)
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


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_success(mock_post, mock_get_experiments):
    """Test that a valid request with a job of type 'AUTOREDUCTION' returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_invalid_file(mock_post, mock_get_experiments):
    """Test that a 404 is returned when an invalid file name is supplied."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/invalid_filename.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_unauthorized(mock_post, mock_get_experiments):
    """Test that a request without authentication returns 403."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe")

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_invalid_job(mock_post):
    """Test that a 404 is returned for an invalid job ID."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/job/99999/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_no_owner(mock_post, mock_get_experiments, mock_get_job):
    """Test that an internal server error is returned with when a job has the type 'AUTOREDUCED' and the owner is
    missing."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner = None
    response = client.get("/job/5001/filename/test.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Job has no owner" in response.text


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_experiment_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that an internal server error is returned with when a job has the type 'AUTOREDUCED' and the experiment
    number is missing."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.experiment_number = None
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Experiment number not found" in response.text


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple(mock_post, mock_get_experiments, mock_get_job):
    """Test that a valid request with a job of type 'SIMPLE' returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.job_type = JobType.SIMPLE
    mock_get_job.return_value.owner.experiment_number = 20024
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple_and_experiment_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that a valid request with a job of type 'SIMPLE' and no experiment number returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = 20024
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple_and_experiment_and_user_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that an internal server error is returned when the job type is 'SIMPLE' and there is no experiment number
    and user number."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = None
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "User number not found" in response.text


@patch("fia_api.routers.jobs.find_file_user_number")
@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_missing_filepath(mock_post, mock_get_experiments, mock_get_job, mock_find_file):
    """Test that a file not found error is returned in the event the filepath is None."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = 1234
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE
    mock_find_file.return_value = None
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "File not found" in response.text


def test_post_autoreduction_run_doesnt_exist():
    response = client.post(
        "/job/autoreduction",
        json={
            "filename": "test123.nxspe",
            "rb_number": "12345",
            "instrument_name": "TEST",
            "users": "user1, user2",
            "title": "test experiment",
            "run_start": str(datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)),
            "run_end": str(datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)),
            "good_frames": 5,
            "raw_frames": 10,
            "additional_values": {"foo": "bar", "baz": 1},
            "runner_image": "test_runner_image",
        },
        headers=API_KEY_HEADER,
    )

    assert response.status_code == HTTPStatus.CREATED
    with SESSION() as session:
        try:
            run = session.execute(select(Run).order_by(Run.id.desc()).limit(1)).scalar()
            assert run.filename == "test123.nxspe"
            expected_job_id = run.jobs[0].id
            expected_script = run.jobs[0].script.script

            assert response.json()["job_id"] == expected_job_id
            assert response.json()["script"] == expected_script
        finally:
            session.execute(delete(Job).where(Job.id == expected_job_id))
            session.commit()


def test_post_autoreduction_run_exists():
    with SESSION() as session:
        try:
            run = session.execute(select(Run).where(Run.id == 5001).limit(1)).scalar()  # noqa: PLR2004
            response = client.post(
                "/job/autoreduction",
                json={
                    "filename": run.filename,
                    "rb_number": "12345",
                    "instrument_name": "TEST",
                    "users": "user1, user2",
                    "title": "test experiment",
                    "run_start": str(datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)),
                    "run_end": str(datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)),
                    "good_frames": 5,
                    "raw_frames": 10,
                    "additional_values": {"foo": "bar", "baz": 1},
                    "runner_image": "test_runner_image",
                },
                headers=API_KEY_HEADER,
            )
            session.refresh(run)
            assert response.status_code == HTTPStatus.CREATED
            assert response.json()["job_id"] in [job.id for job in run.jobs]
            assert response.json()["script"] in [
                job.script.script if job.script is not None else None for job in run.jobs
            ]
        finally:
            session.execute(delete(Job).where(Job.id == response.json()["job_id"]))
            session.commit()


@patch("fia_api.core.auth.tokens.requests.post")
def test_download_invalid_user_perms(mock_post):
    """Test that a user trying to download a file that doesn't match their credentials returns a 403 status code."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=USER_HEADER)

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_valid_user_perms(mock_post, mock_get_job):
    """Test that a user trying to download a file that does match their credentials returns a 200 status code."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_job.return_value.owner.experiment_number = 20024
    mock_get_job.return_value.instrument.instrument_name = "MARI"
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=USER_HEADER)

    assert response.status_code == HTTPStatus.OK


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_success(mock_post, mock_get_experiments):
    """Test that a valid request returns a zip file containing multiple files."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    # Construct payload with job IDs and filenames
    payload = {"5001": ["MAR29531_10.5meV_sa.nxspe", "MAR29531_10.5meV_sa_copy.nxspe"]}

    response = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == "attachment; filename=reduction_files.zip"

    # Validate the contents of the zip
    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as zipf:
        names = zipf.namelist()
        assert "5001/MAR29531_10.5meV_sa.nxspe" in names
        assert "5001/MAR29531_10.5meV_sa_copy.nxspe" in names


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_with_invalid_file(mock_post, mock_get_experiments):
    """Test that only valid files are zipped when one filename is invalid."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    payload = {"5001": ["MAR29531_10.5meV_sa.nxspe", "nonexistent_file.nxspe"]}

    response = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/zip"

    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as zipf:
        names = zipf.namelist()
        assert "5001/MAR29531_10.5meV_sa.nxspe" in names
        assert "5001/nonexistent_file.nxspe" not in names
