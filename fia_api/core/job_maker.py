import json
from typing import Any

from pika.adapters.blocking_connection import BlockingConnection  # type: ignore[import-untyped]
from pika.connection import ConnectionParameters  # type: ignore[import-untyped]
from pika.credentials import PlainCredentials  # type: ignore[import-untyped]


class JobMaker:
    def __init__(self, queue_host: str, username: str, password: str, queue_name: str):
        # Connect to Rabbit
        credentials = PlainCredentials(username=username, password=password)
        self.connection_parameters = ConnectionParameters(queue_host, 5672, credentials=credentials)
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self._connect_to_broker()

    def _connect_to_broker(self) -> None:
        """
        Use this to connect to the broker
        :return: None
        """
        self.connection = BlockingConnection(self.connection_parameters)
        self.channel = self.connection.channel()  # type: ignore[attr-defined]
        self.channel.exchange_declare(  # type: ignore[attr-defined]
            self.queue_name,
            exchange_type="direct",
            durable=True,
        )
        self.channel.queue_declare(  # type: ignore[attr-defined]
            self.queue_name,
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )
        self.channel.queue_bind(self.queue_name, self.queue_name, routing_key="")  # type: ignore[attr-defined]

    def _send_message(self, message: str) -> None:
        self._connect_to_broker()
        # Assuming channel is set in _connect_to_broker()
        self.channel.basic_publish(exchange=self.queue_name, routing_key="", body=message)  # type: ignore

    def rerun_job(
        self,
        job_id: int,
        runner_image: str,
        script: str,
        experiment_number: int | None = None,
        user_number: int | None = None,
    ) -> None:
        """
        Default to using experiment_number over user_number
        :param job_id:
        :param runner_image:
        :param script:
        :param experiment_number:
        :param user_number:
        :return: None
        """
        json_dict: dict[str, Any] = {"job_id": job_id, "runner_image": runner_image, "script": script}
        if experiment_number is not None:
            json_dict["experiment_number"] = experiment_number
        elif user_number is not None:
            json_dict["user_number"] = user_number
        else:
            raise ValueError("Something needs to own the job, either experiment_number or user_number.")
        self._send_message(json.dumps(json_dict))

    def simple_job(
        self, runner_image: str, script: str, experiment_number: int | None = None, user_number: int | None = None
    ) -> None:
        """
        Default to using experiment_number over user_number
        :param runner_image:
        :param script:
        :param experiment_number:
        :param user_number:
        :return: None
        """
        json_dict: dict[str, Any] = {"runner_image": runner_image, "script": script}
        if experiment_number is not None:
            json_dict["experiment_number"] = experiment_number
        elif user_number is not None:
            json_dict["user_number"] = user_number
        else:
            raise ValueError("Something needs to own the job, either experiment_number or user_number.")
        self._send_message(json.dumps(json_dict))
