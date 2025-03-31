from __future__ import annotations

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from db.data_models import Job, JobOwner, JobType, Script, State
from pika.adapters.blocking_connection import BlockingConnection  # type: ignore[import-untyped]
from pika.connection import ConnectionParameters  # type: ignore[import-untyped]
from pika.credentials import PlainCredentials  # type: ignore[import-untyped]

from fia_api.core.exceptions import JobRequestError
from fia_api.core.repositories import Repo
from fia_api.core.specifications.job import JobSpecification
from fia_api.core.specifications.job_owner import JobOwnerSpecification
from fia_api.core.specifications.script import ScriptSpecification

logger = logging.getLogger(__name__)


def hash_script(script: str) -> str:
    """
    Given a script, return the sha512 hash of the script
    :param script: the script to hash
    :return: The script hash
    """
    return hashlib.sha512(script.encode()).hexdigest()


def require_owner(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure that either a user_number or experiment_number is provided to the function. if not, raise a
    JobRequestError
    :param func: The function to wrap
    :return: The wrapped function
    """

    @functools.wraps(func)
    def wrapper(self: JobMaker, *args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
        if kwargs.get("user_number") is None and kwargs.get("experiment_number") is None:
            raise JobRequestError("Something needs to own the job, either experiment_number or user_number.")
        return func(self, *args, **kwargs)

    return wrapper


class JobMaker:
    def __init__(self, queue_host: str, username: str, password: str, queue_name: str):
        credentials = PlainCredentials(username=username, password=password)
        self._job_repo: Repo[Job] = Repo()
        self._owner_repo: Repo[JobOwner] = Repo()
        self._script_repo: Repo[Script] = Repo()
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

    @require_owner
    def create_rerun_job(
        self,
        job_id: int,
        runner_image: str,
        script: str,
        experiment_number: int | None = None,
        user_number: int | None = None,
    ) -> None:
        """
        Submit a rerun job to the scheduled job queue in the message broker. Default to using experiment_number over
        user_number.
        :param job_id: The id of the job to be reran
        :param runner_image: The image used as a runner on the cluster
        :param script: The script to be used in the runner
        :param experiment_number: the experiment number of the owner
        :param user_number: the user number of the owner
        :return: None
        """
        original_job = self._job_repo.find_one(JobSpecification().by_id(job_id))
        if original_job is None:
            raise JobRequestError("Cannot rerun job that does not exist.")

        job_owner = self._owner_repo.find_one(
            JobOwnerSpecification().by_values(experiment_number=experiment_number, user_number=user_number)
        )
        if job_owner is None:
            job_owner = JobOwner(experiment_number=experiment_number, user_number=user_number)

        script_hash = hash_script(script)
        script_object = self._script_repo.find_one(ScriptSpecification().by_script_hash(script_hash))
        if script_object is None:
            script_object = Script(script=script, script_hash=hash_script(script))

        rerun_job = Job(
            owner_id=job_owner.id,
            job_type=JobType.RERUN,
            runner_image=runner_image,
            script=script_object,
            state=State.NOT_STARTED,
            instrument_id=original_job.instrument_id,
            inputs={},
            run=original_job.run,
        )

        rerun_job = self._job_repo.add_one(rerun_job)

        instrument = None
        rb_number = 0
        filename = None
        if rerun_job.run:
            filename = rerun_job.run.filename
            instrument = rerun_job.run.instrument.instrument_name
            if rerun_job.run.owner and rerun_job.run.owner.experiment_number:
                rb_number = rerun_job.run.owner.experiment_number

        if instrument is None or filename is None:
            raise JobRequestError("Cannot create rerun job with missing run information.")

        json_dict: dict[str, Any] = {
            "filename": Path(filename).stem,
            "instrument": instrument,
            "rb_number": rb_number,
            "job_id": rerun_job.id,
            "runner_image": runner_image,
            "script": script,
        }
        self._send_message(json.dumps(json_dict))

    @require_owner
    def create_simple_job(
        self, runner_image: str, script: str, experiment_number: int | None = None, user_number: int | None = None
    ) -> None:
        """
        Submit a job to the scheduled job queue in the message broker. Default to using experiment_number over
        user_number.
        :param runner_image: The image used as a runner on the cluster
        :param script: The script to be used in the runner
        :param experiment_number: the experiment number of the owner
        :param user_number: the user number of the owner
        :return: None
        """

        job_owner = self._owner_repo.find_one(
            JobOwnerSpecification().by_values(experiment_number=experiment_number, user_number=user_number)
        )
        if job_owner is None:
            job_owner = JobOwner(experiment_number=experiment_number, user_number=user_number)

        job = Job(
            owner=job_owner,
            job_type=JobType.SIMPLE,
            runner_image=runner_image,
            script=Script(script=script, script_hash=hash_script(script)),
            state=State.NOT_STARTED,
            inputs={},
        )
        job = self._job_repo.add_one(job)

        message_dict: dict[str, Any] = {
            "runner_image": runner_image,
            "script": script,
            "experiment_number": experiment_number,
            "user_number": user_number,
            "job_id": job.id,
        }
        self._send_message(json.dumps(message_dict))
