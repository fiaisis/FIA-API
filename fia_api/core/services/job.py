"""Service Layer for jobs"""

import os
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.exceptions import AuthError, MissingRecordError
from fia_api.core.job_maker import JobMaker
from fia_api.core.models import Instrument, Job, JobOwner, JobType, Run, Script, State
from fia_api.core.repositories import Repo
from fia_api.core.request_models import AutoreductionRequest, PartialJobUpdateRequest
from fia_api.core.specifications.filters import apply_filters_to_spec
from fia_api.core.specifications.instrument import InstrumentSpecification
from fia_api.core.specifications.job import JobSpecification
from fia_api.core.specifications.job_owner import JobOwnerSpecification
from fia_api.core.specifications.run import RunSpecification
from fia_api.core.specifications.script import ScriptSpecification
from fia_api.core.utility import hash_script
from fia_api.scripts.acquisition import get_script_for_job


def job_maker() -> JobMaker:
    """Creates a JobMaker and returns it using env vars"""
    queue_host = os.environ.get("QUEUE_HOST", "localhost")
    queue_name = os.environ.get("EGRESS_QUEUE_NAME", "scheduled-jobs")
    producer_username = os.environ.get("QUEUE_USER", "guest")
    producer_password = os.environ.get("QUEUE_PASSWORD", "guest")
    return JobMaker(
        queue_host=queue_host, queue_name=queue_name, username=producer_username, password=producer_password
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

_JOB_REPO: Repo[Job] = Repo()
_RUN_REPO: Repo[Run] = Repo()
_INSTRUMENT_REPO: Repo[Instrument] = Repo()
_OWNER_REPO: Repo[JobOwner] = Repo()
_SCRIPT_REPO: Repo[Script] = Repo()


def get_job_by_instrument(
    instrument: str,
    limit: int = 100,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
    filters: Mapping[str, Any] | None = None,
) -> Sequence[Job]:
    """
    Given an instrument name return a sequence of jobs for that instrument. Optionally providing a limit and
    offset to be applied to the sequence
    :param instrument: (str) - The instrument to get by
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :param user_number: (optional[str]) The user number of who is making the request
    :param filters: Optional Mapping[str,Any] the filters to be applied to the query
    :return: Sequence of Jobs for an instrument
    """
    specification = JobSpecification().by_instruments(
        instruments=[instrument],
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        user_number=user_number,
    )
    if filters:
        specification = apply_filters_to_spec(filters, specification)
    return _JOB_REPO.find(specification)


def get_all_jobs(
    limit: int = 100,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
    filters: Mapping[str, Any] | None = None,
) -> Sequence[Job]:
    """
    Get all jobs, if a user number is provided then only the jobs that user has permission for will be
    provided.
    :param user_number:  Optional user number to filter with
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :param filters: Optional Mapping[str,Any] the filters to be applied
    :return: A Sequence of Jobs
    """
    specification = JobSpecification()
    if user_number is None:
        specification = specification.all(
            limit=limit, offset=offset, order_by=order_by, order_direction=order_direction
        )
    else:
        experiment_numbers = get_experiments_for_user_number(user_number)
        specification = specification.by_experiment_numbers(
            experiment_numbers, limit=limit, offset=offset, order_by=order_by, order_direction=order_direction
        )
    if filters:
        apply_filters_to_spec(filters, specification)

    return _JOB_REPO.find(specification)


def get_job_by_id(job_id: int, user_number: int | None = None) -> Job:
    """
    Given an ID return the jobs with that ID
    :param job_id: The id of the jobs to search for
    :return: The job
    :raises: MissingRecordError when no jobs for that ID is found
    """
    job = _JOB_REPO.find_one(JobSpecification().by_id(job_id))
    if job is None:
        raise MissingRecordError(f"No Job for id {job_id}")

    if user_number:
        experiments = get_experiments_for_user_number(user_number)
        if job.owner is None or (
            job.owner.experiment_number not in experiments and job.owner.user_number != user_number
        ):
            raise AuthError("User does not have permission for job")

    return job


def count_jobs_by_instrument(instrument: str, filters: Mapping[str, Any]) -> int:
    """
    Given an instrument name, count the jobs for that instrument
    :param instrument: Instruments to count from
    :return: Number of jobs
    """
    spec = JobSpecification().by_instruments(instruments=[instrument])
    if filters:
        spec = apply_filters_to_spec(filters, spec)
    return _JOB_REPO.count(spec)


def count_jobs(filters: Mapping[str, Any] | None = None) -> int:
    """
    Count the total number of jobs
    :return: (int) number of jobs
    """
    spec = JobSpecification().all()
    if filters:
        spec = apply_filters_to_spec(filters, spec)
    return _JOB_REPO.count(spec)


def get_experiment_number_for_job_id(job_id: int) -> int:
    """
    Given a job id find and return the experiment number attached to it or will raise an exception.
    :param job_id: (int) The id of the job
    :return: (int) the experiment number of the job found with the id
    """
    job = _JOB_REPO.find_one(JobSpecification().by_id(job_id))
    if job is not None:
        owner = job.owner
        if owner is not None and owner.experiment_number is not None:
            return owner.experiment_number
        raise ValueError("Job has no owner or owner does not have an experiment number in the DB")
    raise ValueError("No job found with ID in the DB")


def update_job_by_id(id_: int, job: PartialJobUpdateRequest) -> Job:
    """
    Update the given job in the database. This is a safe update as it will only update fields that should be updated,
    and not update those that shouldn't. I.E no retroactive changing of IDs etc.
    :param id_: (int) The id of the job to update
    :param job: The job to update with
    :return: The updated job
    """
    original_job = _JOB_REPO.find_one(JobSpecification().by_id(id_))
    if original_job is None:
        raise MissingRecordError(f"No job found with id {id_}")
    # We only update the fields that should change, not those that should never e.g. script, inputs.
    # The start is included because it is recorded based from the pod start, end time post job run
    for attr in ["state", "end", "start", "status_message", "outputs", "stacktrace"]:
        value = getattr(job, attr)
        if value is not None:
            setattr(original_job, attr, value)

    return _JOB_REPO.update_one(original_job)


def create_autoreduction_job(job_request: AutoreductionRequest) -> Job:
    """
    Create an autoreduction job in the system based on a provided request.

    This method constructs a new job for the autoreduction process. If the run associated with
    the job request already exists, it is used. If not, the required run and associated entities
    (instrument, owner) are created. The method also handles the script generation and hashing.

    :param job_request: (AutoreductionRequest) The job creation request data containing information
                        about the run, instrument name, experiment number, and other related metadata.
    :return: The created Job instance.
    """

    run = _RUN_REPO.find_one(RunSpecification().by_filename(job_request.filename))

    if run:
        job = Job(
            start=None,
            end=None,
            state=State.NOT_STARTED,
            inputs=job_request.additional_values,
            script_id=None,
            outputs=None,
            runner_image=job_request.runner_image,
            job_type=JobType.AUTOREDUCTION,
            run_id=run.id,
            owner_id=run.owner_id,
            instrument_id=run.instrument_id,
        )
        instrument = run.instrument

    else:
        instrument = _INSTRUMENT_REPO.find_one(InstrumentSpecification().by_name(job_request.instrument_name))  # type: ignore # The above declaration is guaranteed to be not None, but mypy cannot know this
        if instrument is None:
            instrument = _INSTRUMENT_REPO.add_one(Instrument(instrument_name=job_request.instrument_name))
        owner = _OWNER_REPO.find_one(
            JobOwnerSpecification().by_values(experiment_number=int(job_request.rb_number), user_number=None)
        )
        if owner is None:
            owner = _OWNER_REPO.add_one(JobOwner(experiment_number=int(job_request.rb_number)))
        run = _RUN_REPO.add_one(
            Run(
                title=job_request.title,
                users=job_request.users,
                run_start=job_request.run_start,
                run_end=job_request.run_end,
                filename=job_request.filename,
                owner_id=owner.id,
                instrument_id=instrument.id,
                good_frames=job_request.good_frames,
                raw_frames=job_request.raw_frames,
            )
        )

        job = Job(
            start=None,
            end=None,
            state=State.NOT_STARTED,
            inputs=job_request.additional_values,
            script_id=None,
            outputs=None,
            runner_image=job_request.runner_image,
            job_type=JobType.AUTOREDUCTION,
            run_id=run.id,
            owner_id=owner.id,
            instrument_id=instrument.id,
            instrument=instrument,
        )

    job.run = run
    pre_script = get_script_for_job(instrument.instrument_name, job)
    job.run = None
    job.run_id = run.id
    script = _SCRIPT_REPO.find_one(ScriptSpecification().by_script_hash(hash_script(pre_script.value)))
    if script is None:
        script = Script(script=pre_script.value, sha=pre_script.sha)
        job.script = script
    else:
        job.script_id = script.id

    return _JOB_REPO.add_one(job)
