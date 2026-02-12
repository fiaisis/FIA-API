import datetime
from http import HTTPStatus
from unittest.mock import patch

import pytest
from sqlalchemy import delete, select

from fia_api.core.models import Job, Run
from fia_api.core.repositories import SESSION
from fia_api.core.responses import JobResponse
from test.e2e.constants import API_KEY_HEADER, STAFF_HEADER, TEST_JOB, USER_HEADER
from test.e2e.test_core import client


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
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures("_user_owned_data_setup")
def test_update_job_returns_404_when_id_doesn_t_exist():
    new_job = JobResponse.from_job(TEST_JOB)
    new_job.state = "SUCCESSFUL"
    response = client.patch("/job/-42069", headers=API_KEY_HEADER, json=new_job.model_dump(mode="json"))
    assert response.status_code == HTTPStatus.NOT_FOUND


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


def test_json_output_added_to_autoreduced_script():
    script_addon = (
        "import json\n"
        "\n"
        "print(json.dumps({'status': 'Successful', 'status_message':"
        "'','output_files': output, 'stacktrace': ''}))\n"
    )
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
            assert response.status_code == HTTPStatus.CREATED
            assert response.json()["script"].endswith(script_addon)
        finally:
            session.execute(delete(Job).where(Job.id == response.json()["job_id"]))
            session.commit()


def test_get_live_data_instruments():
    """Test that the live data instruments endpoint returns a list"""
    response = client.get("/live-data/instruments")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)
