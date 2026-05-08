import json
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from sqlalchemy import func, select
from starlette.testclient import TestClient

from fia_api.core.models import Job
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


@patch('fia_api.core.job_maker.BlockingConnection')
def test_post_resubmit_job_success(mock_blocking_connection):
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_blocking_connection.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    response = client.post("/job/resubmit", json={"job_id": 1}, headers=API_KEY_HEADER)

    assert response.status_code == HTTPStatus.OK
    mock_channel.basic_publish.assert_called_once()
    _, kwargs = mock_channel.basic_publish.call_args
    assert kwargs['exchange'] == 'watched-files'
    assert 'full/path/to/file.nxs' in kwargs['body']


def test_post_resubmit_job_not_found():
    response = client.post("/job/resubmit", json={"job_id": 9999}, headers=API_KEY_HEADER)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Cannot rerun job that does not exist."}


@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_resubmit_unauthorized(mock_get_experiments, mock_auth_post):
    # Setup: Mock auth as a regular user (user_number 1234)
    mock_auth_post.return_value.status_code = HTTPStatus.OK
    # Mock user experiments to NOT include the experiment for the target job
    mock_get_experiments.return_value = [999] 
    
    # 1. Target a job ID that belongs to experiment 1820497 (which the user doesn't have)
    target_job_id = 5001 
    
    # 2. Call the endpoint as a non-staff user
    response = client.post(
        "/job/resubmit", 
        json={"job_id": target_job_id}, 
        headers=USER_HEADER
    )
    
    # 3. Assert the response is 403 Forbidden
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "User does not have permission" in response.json()["detail"]
    

@patch("fia_api.core.auth.tokens.requests.post")
def test_resubmit_job_not_found(mock_auth_post):
    # Setup: Mock auth to allow the request as staff
    mock_auth_post.return_value.status_code = HTTPStatus.OK
    
    # 1. Choose an ID that definitely doesn't exist
    non_existent_id = 999999
    
    # 2. Call the endpoint
    response = client.post(
        "/job/resubmit", 
        json={"job_id": non_existent_id}, 
        headers=STAFF_HEADER
    )
    
    # 3. Assert the response is 404
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "No Job for id" in response.json()["detail"]
    


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
