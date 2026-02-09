"""Service Layer for jobs"""

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.auth.tokens import User
from fia_api.core.exceptions import AuthError, DataIntegrityError, JobOwnerError, MissingRecordError
from fia_api.core.job_maker import JobMaker
from fia_api.core.models import Instrument, Job, JobOwner, JobType, Run, Script, State
from fia_api.core.repositories import Repo
from fia_api.core.request_models import AutoreductionRequest, PartialJobUpdateRequest
from fia_api.core.session import get_db_session
from fia_api.core.specifications.filters import apply_filters_to_spec
from fia_api.core.specifications.instrument import InstrumentSpecification
from fia_api.core.specifications.job import JobSpecification
from fia_api.core.specifications.job_owner import JobOwnerSpecification
from fia_api.core.specifications.run import RunSpecification
from fia_api.core.specifications.script import ScriptSpecification
from fia_api.core.utility import (
    find_file_experiment_number,
    find_file_instrument,
    find_file_user_number,
    get_packages,
    hash_script,
)
from fia_api.scripts.acquisition import get_script_for_job


def job_maker(session: Annotated[Session, Depends(get_db_session)]) -> JobMaker:
    """Creates a JobMaker and returns it using env vars"""
    queue_host = os.environ.get("QUEUE_HOST", "localhost")
    queue_name = os.environ.get("EGRESS_QUEUE_NAME", "scheduled-jobs")
    producer_username = os.environ.get("QUEUE_USER", "guest")
    producer_password = os.environ.get("QUEUE_PASSWORD", "guest")
    return JobMaker(
        queue_host=queue_host,
        queue_name=queue_name,
        username=producer_username,
        password=producer_password,
        db=session,
    )


class SimpleJob(BaseModel):
    runner_image: str
    script: str


class FastStartJob(BaseModel):
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


def get_job_by_instrument(
    instrument: str,
    session: Session,
    limit: int = 100,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
    filters: Mapping[str, Any] | None = None,
    exclude_fast_start_jobs: bool = False,
) -> Sequence[Job]:
    """
    Given an instrument name return a sequence of jobs for that instrument. Optionally providing a limit and
    offset to be applied to the sequence
    :param instrument: (str) - The instrument to get by
    :param session: The current session of the request
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :param user_number: (optional[str]) The user number of who is making the request
    :param filters: Optional Mapping[str,Any] the filters to be applied to the query
    :param exclude_fast_start_jobs: (bool) Whether to exclude fast start jobs
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
    if exclude_fast_start_jobs:
        specification = apply_filters_to_spec({"job_type_not_in": [JobType.FAST_START]}, specification)
    job_repo: Repo[Job] = Repo(session)
    return job_repo.find(specification)


def get_all_jobs(
    session: Session,
    limit: int = 100,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
    filters: Mapping[str, Any] | None = None,
    exclude_fast_start_jobs: bool = False,
) -> Sequence[Job]:
    """
    Get all jobs, if a user number is provided then only the jobs that user has permission for will be
    provided.
    :param session: The current session of the request
    :param user_number:  Optional user number to filter with
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of jobs to offset the sequence from the entire job set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :param filters: Optional Mapping[str,Any] the filters to be applied
    :param exclude_fast_start_jobs: (bool) Whether to exclude fast start jobs
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
        specification = apply_filters_to_spec(filters, specification)
    if exclude_fast_start_jobs:
        specification = apply_filters_to_spec({"job_type_not_in": [JobType.FAST_START]}, specification)
    job_repo: Repo[Job] = Repo(session)
    return job_repo.find(specification)


def get_job_by_id(
    job_id: int,
    session: Session,
    user_number: int | None = None,
) -> Job:
    """
    Given an ID return the jobs with that ID
    :param job_id: The id of the jobs to search for
    :param session: The current session of the request
    :return: The job
    :raises: MissingRecordError when no jobs for that ID is found
    """
    job_repo: Repo[Job] = Repo(session)
    job = job_repo.find_one(JobSpecification().by_id(job_id))
    if job is None:
        raise MissingRecordError(f"No Job for id {job_id}")

    if user_number:
        experiments = get_experiments_for_user_number(user_number)
        if job.owner is None or (
            job.owner.experiment_number not in experiments and job.owner.user_number != user_number
        ):
            raise AuthError("User does not have permission for job")

    return job


def count_jobs_by_instrument(
    instrument: str,
    session: Session,
    filters: Mapping[str, Any] | None,
    exclude_fast_start_jobs: bool = False,
) -> int:
    """
    Given an instrument name, count the jobs for that instrument
    :param instrument: Instruments to count from
    :param session: The current session of the request
    :param exclude_fast_start_jobs: (bool) Whether to exclude fast start jobs
    :return: Number of jobs
    """
    spec = JobSpecification().by_instruments(instruments=[instrument])
    if filters:
        spec = apply_filters_to_spec(filters, spec)
    if exclude_fast_start_jobs:
        spec = apply_filters_to_spec({"job_type_not_in": [JobType.FAST_START]}, spec)
    job_repo: Repo[Job] = Repo(session)
    return job_repo.count(spec)


def count_jobs(
    session: Session,
    filters: Mapping[str, Any] | None = None,
    exclude_fast_start_jobs: bool = False,
) -> int:
    """
    Count the total number of jobs
    :param filters: Optional Mapping[str,Any] the filters to be applied
    :param session: The current session of the request
    :param exclude_fast_start_jobs: (bool) Whether to exclude fast start jobs
    :return: (int) number of jobs
    """
    spec = JobSpecification().all()
    if filters:
        spec = apply_filters_to_spec(filters, spec)
    if exclude_fast_start_jobs:
        spec = apply_filters_to_spec({"job_type_not_in": [JobType.FAST_START]}, spec)
    job_repo: Repo[Job] = Repo(session)
    return job_repo.count(spec)


def get_experiment_number_for_job_id(job_id: int, session: Session) -> int:
    """
    Given a job id find and return the experiment number attached to it or will raise an exception.
    :param job_id: (int) The id of the job
    :param session: The current session of the request
    :return: (int) the experiment number of the job found with the id
    """
    job_repo: Repo[Job] = Repo(session)
    job = job_repo.find_one(JobSpecification().by_id(job_id))
    if job is not None:
        owner = job.owner
        if owner is not None and owner.experiment_number is not None:
            return owner.experiment_number
        raise ValueError("Job has no owner or owner does not have an experiment number in the DB")
    raise ValueError("No job found with ID in the DB")


def update_job_by_id(id_: int, job: PartialJobUpdateRequest, session: Session) -> Job:
    """
    Update the given job in the database. This is a safe update as it will only update fields that should be updated,
    and not update those that shouldn't. I.E no retroactive changing of IDs etc.
    :param id_: (int) The id of the job to update
    :param job: The job to update with
    :param session: The current session of the request
    :return: The updated job
    """
    job_repo: Repo[Job] = Repo(session)
    original_job = job_repo.find_one(JobSpecification().by_id(id_))
    if original_job is None:
        raise MissingRecordError(f"No job found with id {id_}")
    # We only update the fields that should change, not those that should never e.g. script, inputs.
    # The start is included because it is recorded based from the pod start, end time post job run
    for attr in ["state", "end", "start", "status_message", "outputs", "stacktrace"]:
        value = getattr(job, attr)
        if value is not None:
            setattr(original_job, attr, value)

    return job_repo.update_one(original_job)


def create_autoreduction_job(job_request: AutoreductionRequest, session: Session) -> Job:
    """
    Create an autoreduction job in the system based on a provided request.

    This method constructs a new job for the autoreduction process. If the run associated with
    the job request already exists, it is used. If not, the required run and associated entities
    (instrument, owner) are created. The method also handles the script generation and hashing.

    :param job_request: (AutoreductionRequest) The job creation request data containing information
                        about the run, instrument name, experiment number, and other related metadata.
    :param session: The current session of the request
    :return: The created Job instance.
    """
    run_repo: Repo[Run] = Repo(session)
    run = run_repo.find_one(RunSpecification().by_filename(job_request.filename))

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
        instrument_repo: Repo[Instrument] = Repo(session)
        owner_repo: Repo[JobOwner] = Repo(session)
        instrument = instrument_repo.find_one(InstrumentSpecification().by_name(job_request.instrument_name))  # type: ignore # The above declaration is guaranteed to be not None, but mypy cannot know this
        if instrument is None:
            instrument = instrument_repo.add_one(Instrument(instrument_name=job_request.instrument_name))
        owner = owner_repo.find_one(
            JobOwnerSpecification().by_values(experiment_number=int(job_request.rb_number), user_number=None)
        )
        if owner is None:
            owner = owner_repo.add_one(JobOwner(experiment_number=int(job_request.rb_number)))
        run = run_repo.add_one(
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

    pre_script = get_script_for_job(instrument.instrument_name, job)
    script_repo: Repo[Script] = Repo(session)
    script = script_repo.find_one(ScriptSpecification().by_script_hash(hash_script(pre_script.value)))
    if script is None:
        script = Script(script=pre_script.value, sha=pre_script.sha)
        job.script = script
    else:
        job.script_id = script.id
    job_repo: Repo[Job] = Repo(session)
    return job_repo.add_one(job)


def resolve_job_files(
    job_files: dict[str, list[str]], user: User, ceph_dir: str, session: Session
) -> tuple[list[tuple[int, str, str]], list[str]]:
    """
    Return a tuple of job_id int, filename string, and filepath string

    :param job_files: dictionary to hold files for zipping and downloading
    :param user: the user requesting files to be zipped and downloaded
    :param ceph_dir: the base directory
    """
    resolved_files: list[tuple[int, str, str]] = []
    missing_files: list[str] = []

    for job_id_str, filenames in job_files.items():
        job_id = int(job_id_str)
        job = (
            get_job_by_id(job_id, session)
            if user.role == "staff"
            else get_job_by_id(job_id, session, user_number=user.user_number)
        )

        if job.owner is None:
            continue

        for filename in filenames:
            if job.job_type != JobType.SIMPLE and job.owner.experiment_number and job.instrument:
                filepath = find_file_instrument(
                    ceph_dir,
                    job.instrument.instrument_name,
                    int(job.owner.experiment_number),
                    filename,
                )
            elif job.owner.experiment_number:
                filepath = find_file_experiment_number(
                    ceph_dir,
                    int(job.owner.experiment_number),
                    filename,
                )
            elif job.owner.user_number:
                filepath = find_file_user_number(
                    ceph_dir,
                    int(job.owner.user_number),
                    filename,
                )
            else:
                filepath = None

            if filepath and Path(filepath).is_file():
                resolved_files.append((job_id, filename, str(filepath)))
            else:
                missing_files.append(f"{job_id}/{filename}")

    return resolved_files, missing_files


def resolve_job_file_path(job_id: int, filename: str, user: User, ceph_dir: str, session: Session) -> str:
    """
    Return a string with the filepath leading to the passed filename

    :param job_id: the id of the job requesting the file
    :param filename: the name of the file to search for
    :param user: the user requesting the file for download
    :param ceph_dir: the base directory
    """
    job = (
        get_job_by_id(job_id, session)
        if user.role == "staff"
        else get_job_by_id(job_id, session, user_number=user.user_number)
    )

    if job.owner is None:
        raise JobOwnerError("Job has no owner.")

    if job.job_type != JobType.SIMPLE:
        if job.owner.experiment_number is None:
            raise DataIntegrityError("Experiment number not found in scenario where it should be expected.")
        if job.instrument is None:
            raise DataIntegrityError("Instrument not found in scenario where it should be expected.")
        filepath = find_file_instrument(
            ceph_dir=ceph_dir,
            instrument=job.instrument.instrument_name,
            experiment_number=int(job.owner.experiment_number),
            filename=filename,
        )
    elif job.owner.experiment_number is not None:
        filepath = find_file_experiment_number(
            ceph_dir=ceph_dir,
            experiment_number=int(job.owner.experiment_number),
            filename=filename,
        )
    else:
        if job.owner.user_number is None:
            raise DataIntegrityError("User number not found in scenario where it should be expected.")
        filepath = find_file_user_number(
            ceph_dir=ceph_dir,
            user_number=int(job.owner.user_number),
            filename=filename,
        )

    if not filepath or not Path(filepath).is_file():
        raise MissingRecordError("File not found.")

    return str(filepath)


def list_mantid_runners() -> dict[str, str]:
    """
    Get mantid runners from github packages.
    Returns a dict of mantid versions and their corresponding git sha from GitHub.
    """
    data = get_packages(org="fiaisis", image_name="mantid")
    mantid_versions: dict[str, str] = {}
    for item in data:
        name = str(item.get("name", ""))
        tags = item.get("metadata", {}).get("container", {}).get("tags", [])
        if not tags:  # if tags is an empty list
            continue
        mantid_versions[name] = str(tags[0])

    return mantid_versions
