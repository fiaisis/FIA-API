"""end-to-end tests"""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from starlette.testclient import TestClient

from fia_api.core.models import Instrument, Job, JobOwner, Run
from fia_api.fia_api import app
from utils.db_generator import SESSION

from .constants import STAFF_HEADER, TEST_JOB, TEST_RUN, USER_HEADER

client = TestClient(app)

TEST_RUN.jobs.append(TEST_JOB)


def test_get_job_by_id_no_token_results_in_http_forbidden():
    """
    Test 404 for job not existing
    :return:
    """
    response = client.get("/job/123144324234234234")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


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
    expected_experiment_number = 0
    with SESSION() as session:
        job = session.scalar(
            select(Job).join(JobOwner).where(JobOwner.experiment_number is not None).limit(1)
        )  # not the first or the last job
        expected_experiment_number = job.owner.experiment_number
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get(
        f'/jobs?include_run=true&filters={{"experiment_number_in": [{expected_experiment_number}]}}',
        headers=STAFF_HEADER,
    )
    data = response.json()
    assert len(data) == 1
    assert data[0]["run"]["experiment_number"] == expected_experiment_number


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_with_filters(mock_post):
    """Test count with filter"""
    expected_count = 0
    with SESSION() as session:
        expected_count = session.scalar(select(func.count()).select_from(Job).join(Run).where(Run.title.icontains("n")))
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get('/jobs/count?filters={"title":"n"}')
    assert response.json()["count"] == expected_count


@patch("fia_api.core.auth.tokens.requests.post")
def test_count_jobs_by_instrument_with_filter(mock_post):
    """Test count by instrument with filter"""
    expected_count = 0
    with SESSION() as session:
        expected_count = session.scalar(
            select(func.count())
            .select_from(Job)
            .join(Run)
            .join(Instrument)
            .where(Run.title.icontains("n"))
            .where(Instrument.instrument_name == "MARI")
        )

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
                "git_sha": "abc1234567",
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
                "git_sha": "abc1234567",
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
            "git_sha": "abc1234567",
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
    assert response.status_code == HTTPStatus.UNAUTHORIZED


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
                    "git_sha": "abc1234567",
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
                "git_sha": "abc1234567",
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
                "git_sha": "abc1234567",
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
                "git_sha": "abc1234567",
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
