import json
from http import HTTPStatus
from typing import Any

import pytest
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from starlette.testclient import TestClient

from fia_api.fia_api import app

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

    response = client.post("/job/rerun", json=rerun_body, headers={"Authorization": "Bearer shh"})

    message = consume_all_messages(producer_channel)
    assert response.status_code == HTTPStatus.OK
    assert message == [
        {
            "experiment_number": 882000,
            "job_id": 1,
            "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
            "script": 'print("Hello World!")',
        }
    ]


def test_post_simple_job(producer_channel):
    simple_body = {"runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234", "script": 'print("Hello World!")'}

    response = client.post("/job/simple", json=simple_body, headers={"Authorization": "Bearer shh"})

    message = consume_all_messages(producer_channel)
    assert response.status_code == HTTPStatus.OK
    assert message == [
        {
            "runner_image": "ghcr.io/fiaisis/cool-runner@sha256:1234",
            "script": 'print("Hello World!")',
            "user_number": 123,
        }
    ]
