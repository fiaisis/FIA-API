"""
Service Layer for jobs
"""
import os
from collections.abc import Sequence
from typing import Literal

from db.data_models import Job
from pydantic import BaseModel

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.exceptions import AuthenticationError, MissingRecordError
from fia_api.core.job_maker import JobMaker
from fia_api.core.repositories import Repo
from fia_api.core.specifications.job import JobSpecification

QUEUE_HOST = os.environ.get("QUEUE_HOST", "localhost")
QUEUE_NAME = os.environ.get("EGRESS_QUEUE_NAME", "scheduled-jobs")
PRODUCER_USERNAME = os.environ.get("QUEUE_USER", "guest")
PRODUCER_PASSWORD = os.environ.get("QUEUE_PASSWORD", "guest")

JOB_MAKER = JobMaker(
    queue_host=QUEUE_HOST, queue_name=QUEUE_NAME, username=PRODUCER_USERNAME, password=PRODUCER_PASSWORD
)


class SimpleJob(BaseModel):
    runner_image: str
    script: str


class RerunJob(BaseModel):
    job_id: int
    runner_image: str
    script: str


OrderField = Literal[
    "start",
    "end",
    "state",
    "id",
    "run_start",
    "run_end",
    "outputs",
    "experiment_number",
    "experiment_title",
    "filename",
]

_REPO: Repo[Job] = Repo()


def get_job_by_instrument(
    instrument: str,
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
) -> Sequence[Job]:
    """
    Given an instrument name return a sequence of jobs for that instrument. Optionally providing a limit and
    offset to be applied to the sequence
    :param instrument: (str) - The instrument to get by
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :return: Sequence of Jobs for an instrument
    """

    return _REPO.find(
        JobSpecification().by_instrument(
            instrument=instrument,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            user_number=user_number,
        )
    )


def get_all_jobs(
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
) -> Sequence[Job]:
    """
    Get all jobs, if a user number is provided then only the jobs that user has permission for will be
    provided.
    :param user_number:  Optional user number to filter with
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :return: A Sequence of Jobs
    """
    if user_number is None:
        return _REPO.find(
            JobSpecification().all(limit=limit, offset=offset, order_by=order_by, order_direction=order_direction)
        )
    experiment_numbers = get_experiments_for_user_number(user_number)
    return _REPO.find(
        JobSpecification().by_experiment_numbers(
            experiment_numbers, limit=limit, offset=offset, order_direction=order_direction, order_by=order_by
        )
    )


def get_job_by_id(job_id: int, user_number: int | None = None) -> Job:
    """
    Given an ID return the jobs with that ID
    :param job_id: The id of the jobs to search for
    :return: The job
    :raises: MissingRecordError when no jobs for that ID is found
    """
    job = _REPO.find_one(JobSpecification().by_id(job_id))
    if job is None:
        raise MissingRecordError(f"No Job for id {job_id}")

    if user_number:
        experiments = get_experiments_for_user_number(user_number)
        if job.owner is None or (
            job.owner.experiment_number not in experiments and job.owner.user_number != user_number
        ):
            raise AuthenticationError("User does not have permission for job")

    return job


def count_jobs_by_instrument(instrument: str) -> int:
    """
    Given an instrument name, count the jobs for that instrument
    :param instrument: Instrument to count from
    :return: Number of jobs
    """
    return _REPO.count(JobSpecification().by_instrument(instrument=instrument))


def count_jobs() -> int:
    """
    Count the total number of jobs
    :return: (int) number of jobs
    """
    return _REPO.count(JobSpecification().all())


def get_experiment_number_for_job_id(job_id: int) -> int:
    """
    Given a job id find and return the experiment number attached to it or will raise an exception.
    :param job_id: (int) The id of the job
    :return: (int) the experiment number of the job found with the id
    """
    job = _REPO.find_one(JobSpecification().by_id(job_id))
    if job is not None:
        owner = job.owner
        if owner is not None and owner.experiment_number is not None:
            return owner.experiment_number
        raise ValueError("Job has no owner or owner does not have an experiment number in the DB")
    raise ValueError("No job found with ID in the DB")
