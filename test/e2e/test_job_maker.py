import json
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from sqlalchemy import func, select
from starlette.testclient import TestClient

from fia_api.core.models import Instrument, Job, JobOwner, JobType, Run, State
from fia_api.fia_api import app
from utils.db_generator import SESSION

from .constants import API_KEY_HEADER, STAFF_HEADER, USER_HEADER

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def producer_channel() -> BlockingChannel:
    """Consume producer channel fixture"""
    connection = BlockingConnection()
    channel = connection.channel()
    channel.exchange_declare("scheduled-jobs", exchange_type="direct", durable=True)
    channel.queue_declare("scheduled-jobs", durable=True, arguments={"x-queue-type": "quorum"})
    channel.queue_bind("scheduled-jobs", "scheduled-jobs", routing_key="")
    return channel


@pytest.fixture(autouse=True)
def _purge_queues(producer_channel):
    """Purge queues on setup and teardown"""
    yield
    producer_channel.queue_purge(queue="scheduled-jobs")


def consume_all_messages(consumer_channel: BlockingChannel) -> list[dict[str, Any]]:
    """Consume all messages from the queue"""
    received_messages = []
    for mf, _, body in consumer_channel.consume("scheduled-jobs", inactivity_timeout=1):
        if mf is None:
            break

        consumer_channel.basic_ack(mf.delivery_tag)
        received_messages.append(json.loads(body.decode()))
    return received_messages


def produce_message(message: str, channel: BlockingChannel) -> None:
    """
    Given a message and a channel, produce the message to the queue on that channel
    :param message: The message to produce
    :param channel: The channel to produce to
    :return: None
    """
    channel.basic_publish("scheduled-jobs", "", body=message.encode())


def test_post_rerun_job(producer_channel):
    rerun_body = {
        "job_id": "1",
        "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
        "script": 'print("Hello World!")',
    }
    original_job = None
    with SESSION() as session:
        expected_id = session.execute(select(func.count()).select_from(Job)).scalar() + 1
        original_job = session.scalar(select(Job).where(Job.id == 1).join(Job.owner).join(Job.run).join(Job.instrument))
    response = client.post("/job/rerun", json=rerun_body, headers=API_KEY_HEADER)

    message = consume_all_messages(producer_channel)
    assert response.status_code == HTTPStatus.OK
    assert message == [
        {
            "rb_number": original_job.owner.experiment_number,
            "job_id": expected_id,
            "job_type": "rerun",
            "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
            "script": 'print("Hello World!")',
            "filename": str(Path(original_job.run.filename).stem),
            "instrument": original_job.instrument.instrument_name,
        }
    ]


def _make_job_with_run(instrument_name: str, filename: str, run_start: datetime) -> tuple[int, int]:
    """Create an owner/instrument/run/job in the DB with the given instrument, filename and run_start.

    :return: tuple of (job_id, experiment_number)
    """
    with SESSION() as session:
        experiment_number = session.query(func.max(JobOwner.experiment_number)).scalar() + 1
        owner = JobOwner(experiment_number=experiment_number)
        session.add(owner)
        session.flush()

        instrument = session.query(Instrument).filter(Instrument.instrument_name == instrument_name).first()
        if instrument is None:
            instrument = Instrument(instrument_name=instrument_name, specification={})
            session.add(instrument)
            session.flush()

        run = Run(
            filename=filename,
            instrument_id=instrument.id,
            owner_id=owner.id,
            title="Resubmit test run",
            users="User",
            run_start=run_start,
            run_end=run_start,
            good_frames=0,
            raw_frames=0,
        )
        session.add(run)
        session.flush()

        job = Job(owner_id=owner.id, job_type=JobType.SIMPLE, state=State.NOT_STARTED, run_id=run.id, inputs={})
        session.add(job)
        session.commit()
        return job.id, experiment_number


@patch("fia_api.core.job_maker.BlockingConnection")
def test_post_resubmit_job_success(mock_blocking_connection, monkeypatch, tmp_path):
    """A non-IMAT resubmit resolves the bare filename to its full archive path and publishes that."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_blocking_connection.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path))
    monkeypatch.setenv("IMAT_DIR", str(tmp_path / "imat"))

    run_start = datetime(2024, 6, 1, tzinfo=UTC)
    filename = "MARI123456.nxs"
    expected_path = tmp_path / "NDXMARI" / "Instrument" / "data" / "cycle_24_1" / filename
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_text("test file contents")

    job_id, _ = _make_job_with_run("MARI", filename, run_start)

    response = client.post(f"/job/{job_id}/resubmit", json={"job_id": job_id}, headers=API_KEY_HEADER)

    assert response.status_code == HTTPStatus.OK
    mock_channel.basic_publish.assert_called_once()
    _, kwargs = mock_channel.basic_publish.call_args
    assert kwargs["exchange"] == "watched-files"
    assert kwargs["body"] == str(expected_path)


@patch("fia_api.core.job_maker.BlockingConnection")
def test_post_resubmit_job_success_imat(mock_blocking_connection, monkeypatch, tmp_path):
    """An IMAT resubmit resolves the bare filename to a flat path directly under IMAT_DIR."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_blocking_connection.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    imat_dir = tmp_path / "imat"
    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path / "archive"))
    monkeypatch.setenv("IMAT_DIR", str(imat_dir))

    run_start = datetime(2024, 6, 1, tzinfo=UTC)
    filename = "IMAT00038896.nxs"
    imat_dir.mkdir(parents=True, exist_ok=True)
    (imat_dir / filename).write_text("test file contents")

    job_id, _ = _make_job_with_run("IMAT", filename, run_start)

    response = client.post(f"/job/{job_id}/resubmit", json={"job_id": job_id}, headers=API_KEY_HEADER)

    assert response.status_code == HTTPStatus.OK
    mock_channel.basic_publish.assert_called_once()
    _, kwargs = mock_channel.basic_publish.call_args
    assert kwargs["exchange"] == "watched-files"
    assert kwargs["body"] == str(imat_dir / filename)


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_file_not_found(mock_auth_post, monkeypatch, tmp_path):
    """When the input file cannot be located in the archive, resubmit fails with 400 JobRequestError."""
    mock_auth_post.return_value.status_code = HTTPStatus.OK
    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path))
    monkeypatch.setenv("IMAT_DIR", str(tmp_path / "imat"))

    run_start = datetime(2024, 6, 1, tzinfo=UTC)
    filename = "MARI999999.nxs"
    job_id, _ = _make_job_with_run("MARI", filename, run_start)

    response = client.post(f"/job/{job_id}/resubmit", json={"job_id": job_id}, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "The job request was malformed and could not be processed" in response.json()["message"]


def test_post_resubmit_job_not_found():
    response = client.post("/job/9999/resubmit", json={"job_id": 9999}, headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.routers.job_creation.get_experiments_for_user_number")
def test_resubmit_unauthorized(mock_get_experiments, mock_auth_post):
    # Setup: Mock auth as a regular user (user_number 1234)
    mock_auth_post.return_value.status_code = HTTPStatus.OK
    # Mock user experiments to NOT include the experiment for the target job
    mock_get_experiments.return_value = [999]

    # 1. Target a job ID that belongs to experiment 1820497 (which the user doesn't have)
    target_job_id = 5001

    # 2. Call the endpoint as a non-staff user
    response = client.post(f"/job/{target_job_id}/resubmit", json={"job_id": target_job_id}, headers=USER_HEADER)

    # 3. Assert the response is 403 Forbidden
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["message"] == "Forbidden"


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_not_found(mock_auth_post):
    # Setup: Mock auth to allow the request as staff
    mock_auth_post.return_value.status_code = HTTPStatus.OK

    # 1. Choose an ID that definitely doesn't exist
    non_existent_id = 999999

    # 2. Call the endpoint
    response = client.post(f"/job/{non_existent_id}/resubmit", json={"job_id": non_existent_id}, headers=STAFF_HEADER)

    # 3. Assert the response is 404
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["message"] == "Resource not found"


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_no_run(mock_auth_post):
    mock_auth_post.return_value.status_code = HTTPStatus.OK

    # 1. Create a job with NO run_id in the database
    with SESSION() as session:
        owner = session.query(JobOwner).first()
        job = Job(owner_id=owner.id, job_type=JobType.SIMPLE, state=State.NOT_STARTED, run_id=None, inputs={})
        session.add(job)
        session.commit()
        job_id = job.id

    response = client.post(f"/job/{job_id}/resubmit", json={"job_id": job_id}, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "The job request was malformed and could not be processed" in response.json()["message"]


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_missing_filename(mock_auth_post):
    mock_auth_post.return_value.status_code = HTTPStatus.OK

    # 1. Create a job and a run with NO filename
    with SESSION() as session:
        owner = session.query(JobOwner).first()
        instrument = session.query(Instrument).first()

        # Create a run with filename as None
        run = Run(
            filename="",
            instrument_id=instrument.id,
            owner_id=owner.id,
            title="Empty Run",
            users="User",
            run_start=datetime.now(UTC),
            run_end=datetime.now(UTC),
            good_frames=0,
            raw_frames=0,
        )
        session.add(run)
        session.flush()  # get the run.id

        job = Job(owner_id=owner.id, job_type=JobType.SIMPLE, state=State.NOT_STARTED, run_id=run.id, inputs={})
        session.add(job)
        session.commit()
        job_id = job.id
    # 2. Call the endpoint
    response = client.post(f"/job/{job_id}/resubmit", json={"job_id": job_id}, headers=STAFF_HEADER)
    # 3. Assert 400 Bad Request and the specific message
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "The job request was malformed and could not be processed" in response.json()["message"]


@patch("fia_api.core.job_maker.BlockingConnection")
@patch("fia_api.routers.job_creation.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_authorized_user(
    mock_auth_post, mock_get_experiments, mock_blocking_connection, monkeypatch, tmp_path
):
    """Non-staff user whose experiments include the target job's experiment can successfully resubmit."""
    mock_auth_post.return_value.status_code = HTTPStatus.OK
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_blocking_connection.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path))
    monkeypatch.setenv("IMAT_DIR", str(tmp_path / "imat"))

    run_start = datetime(2024, 6, 1, tzinfo=UTC)
    filename = "MARI555555.nxs"
    expected_path = tmp_path / "NDXMARI" / "Instrument" / "data" / "cycle_24_1" / filename
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_text("test file contents")

    job_id, experiment_number = _make_job_with_run("MARI", filename, run_start)

    # Mock experiments to include the target job's experiment number
    mock_get_experiments.return_value = [experiment_number]

    response = client.post(f"/job/{job_id}/resubmit", headers=USER_HEADER)

    assert response.status_code == HTTPStatus.OK
    mock_channel.basic_publish.assert_called_once()
    _, kwargs = mock_channel.basic_publish.call_args
    assert kwargs["exchange"] == "watched-files"
    assert kwargs["body"] == str(expected_path)


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_invalid_token(mock_auth_post):
    """An invalid token that fails both API key and JWT verification returns 403."""
    mock_auth_post.return_value.status_code = HTTPStatus.UNAUTHORIZED

    invalid_header = {"Authorization": "Bearer invalidtoken123"}
    response = client.post("/job/1/resubmit", headers=invalid_header)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["message"] == "Forbidden"


@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_owner_no_experiment_number(mock_auth_post):
    """Job exists but owner has no experiment_number — get_experiment_number_for_job_id raises MissingRecordError."""
    mock_auth_post.return_value.status_code = HTTPStatus.OK

    # Create a job whose owner has no experiment_number
    with SESSION() as session:
        owner = JobOwner(experiment_number=None, user_number=9999)
        session.add(owner)
        session.flush()
        job = Job(owner_id=owner.id, job_type=JobType.SIMPLE, state=State.NOT_STARTED, run_id=None, inputs={})
        session.add(job)
        session.commit()
        job_id = job.id

    response = client.post(f"/job/{job_id}/resubmit", headers=STAFF_HEADER)

    # get_experiment_number_for_job_id raises MissingRecordError → 404
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Resource not found"}


def test_post_simple_job(producer_channel):
    simple_body = {"runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234", "script": 'print("Hello World!")'}
    with SESSION() as session:
        expected_id = session.execute(select(func.count()).select_from(Job)).scalar() + 1
    response = client.post("/job/simple", json=simple_body, headers=API_KEY_HEADER)

    message = consume_all_messages(producer_channel)
    assert response.status_code == HTTPStatus.OK
    assert message == [
        {
            "experiment_number": None,
            "job_type": "simple",
            "job_id": expected_id,
            "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
            "script": 'print("Hello World!")',
            "user_number": -1,  # when auth with api key, the app assumes the pseudo user with user number -1
        }
    ]
