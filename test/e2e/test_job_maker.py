import json
from http import HTTPStatus
from typing import Any

import pytest
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from sqlalchemy import func, select
from starlette.testclient import TestClient

from fia_api.core.models import Job
from fia_api.fia_api import app
from utils.db_generator import SESSION

from .constants import API_KEY_HEADER

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
    with SESSION() as session:
        expected_id = session.execute(select(func.count()).select_from(Job)).scalar() + 1
    response = client.post("/job/rerun", json=rerun_body, headers=API_KEY_HEADER)

    message = consume_all_messages(producer_channel)
    assert response.status_code == HTTPStatus.OK
    assert message == [
        {
            "rb_number": 818853,
            "job_id": expected_id,
            "job_type": "rerun",
            "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
            "script": 'print("Hello World!")',
            "filename": "NILE767455",
            "instrument": "NILE",
        }
    ]


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
