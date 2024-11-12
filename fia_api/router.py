"""
Module containing the REST endpoints
"""

from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.dialects.postgresql import JSONB
from starlette.background import BackgroundTasks

from fia_api.core.auth.api_keys import APIKeyBearer
from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.auth.tokens import JWTBearer, get_user_from_token
from fia_api.core.file_ops import read_dir, write_file_from_remote
from fia_api.core.job_maker import JobMaker
from fia_api.core.repositories import test_connection
from fia_api.core.responses import (
    CountResponse,
    JobResponse,
    JobWithRunResponse,
    PreScriptResponse,
)
from fia_api.core.services.instrument import get_specification_by_instrument_name, update_specification_for_instrument
from fia_api.core.services.job import (
    RerunJob,
    SimpleJob,
    count_jobs,
    count_jobs_by_instrument,
    get_all_jobs,
    get_experiment_number_for_job_id,
    get_job_by_id,
    get_job_by_instrument,
    job_maker,
)
from fia_api.core.utility import safe_check_filepath
from fia_api.scripts.acquisition import (
    get_script_by_sha,
    get_script_for_job,
    write_script_locally,
)
from fia_api.scripts.pre_script import PreScript

ROUTER = APIRouter()
jwt_security = JWTBearer()
api_key_security = APIKeyBearer()


@ROUTER.get("/healthz", tags=["k8s"])
async def get() -> Literal["ok"]:
    """Health Check endpoint."""
    return "ok"


@ROUTER.get("/ready", tags=["k8s"])
async def ready() -> Literal["ok"]:
    try:
        test_connection()
        return "ok"
    except Exception as e:
        raise HTTPException(status_code=503) from e


@ROUTER.get("/instrument/{instrument}/script", tags=["scripts"])
async def get_pre_script(
    instrument: str,
    background_tasks: BackgroundTasks,
    job_id: int | None = None,
) -> PreScriptResponse:
    """
    Script URI - Not intended for calling
    \f
    :param instrument: the instrument
    :param background_tasks: handled by fastapi
    :param job_id: optional query parameter of runfile, used to apply transform
    :return: ScriptResponse
    """
    script = PreScript(value="")
    # This will never be returned from the api, but is necessary for the background task to run
    try:
        script = get_script_for_job(instrument, job_id)
        return script.to_response()
    finally:
        background_tasks.add_task(write_script_locally, script, instrument)
        # write the script after to not slow down request


@ROUTER.get("/instrument/{instrument}/script/sha/{sha}", tags=["scripts"])
async def get_pre_script_by_sha(instrument: str, sha: str, job_id: int | None = None) -> PreScriptResponse:
    """
    Given an instrument and the commit sha of a script, obtain the pre script. Optionally providing a job id to
    transform the script
    \f
    :param instrument: The instrument
    :param sha: The commit sha of the script
    :param job_id: The job id to apply transforms
    :return:
    """
    return get_script_by_sha(instrument, sha, job_id).to_response()


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


@ROUTER.get("/jobs", tags=["jobs"])
async def get_jobs(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_run: bool = False,
) -> list[JobResponse] | list[JobWithRunResponse]:
    """
    Retrieve all jobs.
    \f
    :param credentials: Dependency injected HTTPAuthorizationCredentials
    :param limit: optional limit for the number of jobs returned (default is 0, which can be interpreted as
    no limit)
    :param offset: optional offset for the list of jobs (default is 0)
    :param order_by: Literal["start", "end", "state", "id", "run_start", "run_end", "outputs", "experiment_number",
    "experiment_title", "filename",]
    :param order_direction: Literal["asc", "desc"]
    :param include_run: bool
    :return: List of JobResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    user_number = None if user.role == "staff" else user.user_number
    jobs = get_all_jobs(
        limit=limit, offset=offset, order_by=order_by, order_direction=order_direction, user_number=user_number
    )

    if include_run:
        return [JobWithRunResponse.from_job(j) for j in jobs]
    return [JobResponse.from_job(j) for j in jobs]


@ROUTER.get("/instrument/{instrument}/jobs", tags=["jobs"])
async def get_jobs_by_instrument(
    instrument: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_run: bool = False,
) -> list[JobResponse] | list[JobWithRunResponse]:
    """
    Retrieve a list of jobs for a given instrument.
    \f
    :param credentials: Dependency injected HTTPAuthorizationCredentials
    :param instrument: the name of the instrument
    :param limit: optional limit for the number of jobs returned (default is 0, which can be interpreted as
    no limit)
    :param offset: optional offset for the list of jobs (default is 0)
    :param order_by: Literal["start", "end", "state", "id", "run_start", "run_end", "outputs", "experiment_number",
    "experiment_title", "filename",]
    :param order_direction: Literal["asc", "desc"]
    :param include_run: bool
    :return: List of JobResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    instrument = instrument.upper()
    user_number = None if user.role == "staff" else user.user_number
    jobs = get_job_by_instrument(
        instrument,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        user_number=user_number,
    )

    if include_run:
        return [JobWithRunResponse.from_job(j) for j in jobs]
    return [JobResponse.from_job(j) for j in jobs]


@ROUTER.get("/instrument/{instrument}/jobs/count", tags=["jobs"])
async def count_jobs_for_instrument(
    instrument: str,
) -> CountResponse:
    """
    Count jobs for a given instrument.
    \f
    :param instrument: the name of the instrument
    :return: CountResponse containing the count
    """
    instrument = instrument.upper()
    return CountResponse(count=count_jobs_by_instrument(instrument))


@ROUTER.get("/job/{job_id}", tags=["jobs"])
async def get_job(
    job_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)]
) -> JobWithRunResponse:
    """
    Retrieve a job with nested run data, by iD.
    \f
    :param job_id: the unique identifier of the job
    :return: JobWithRunsResponse object
    """
    user = get_user_from_token(credentials.credentials)
    job = get_job_by_id(job_id) if user.role == "staff" else get_job_by_id(job_id, user_number=user.user_number)
    return JobWithRunResponse.from_job(job)


@ROUTER.get("/jobs/count", tags=["jobs"])
async def count_all_jobs() -> CountResponse:
    """
    Count all jobs
    \f
    :return: CountResponse containing the count
    """
    return CountResponse(count=count_jobs())


@ROUTER.post("/job/rerun", tags=["job"])
async def make_rerun_job(
    rerun_job: RerunJob,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    job_maker: Annotated[JobMaker, Depends(job_maker)],
) -> None:
    user = get_user_from_token(credentials.credentials)
    experiment_number = get_experiment_number_for_job_id(rerun_job.job_id)
    # Forbidden if not staff, and experiment number not related to this user_number's experiment number
    if user.role != "staff":
        experiment_numbers = get_experiments_for_user_number(user.user_number)
        if experiment_number not in experiment_numbers:
            # If not staff this is not allowed
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    job_maker.rerun_job(
        job_id=rerun_job.job_id,
        runner_image=rerun_job.runner_image,
        script=rerun_job.script,
        experiment_number=experiment_number,
    )


@ROUTER.post("/job/simple", tags=["job"])
async def make_simple_job(
    simple_job: SimpleJob,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    job_maker: Annotated[JobMaker, Depends(job_maker)],
) -> None:
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    job_maker.simple_job(runner_image=simple_job.runner_image, script=simple_job.script, user_number=user.user_number)


@ROUTER.get("/instrument/{instrument_name}/specification", tags=["instrument"], response_model=None)
async def get_instrument_specification(
    instrument_name: str, _: Annotated[HTTPAuthorizationCredentials, Depends(api_key_security)]
) -> JSONB | None:
    """
    Return the specification for the given instrument
    \f
    :param instrument_name: The instrument
    :return: The specification
    """
    return get_specification_by_instrument_name(instrument_name.upper())


@ROUTER.put("/instrument/{instrument_name}/specification", tags=["instrument"])
async def update_instrument_specification(
    instrument_name: str,
    specification: dict[str, Any],
    _: Annotated[HTTPAuthorizationCredentials, Depends(api_key_security)],
) -> dict[str, Any]:
    """
    Replace the current specification with the given specification for the given instrument
    \f
    :param instrument_name: The instrument name
    :param specification: The new specification
    :return: The new specification
    """
    update_specification_for_instrument(instrument_name.upper(), specification)
    return specification


@ROUTER.get("/extras", tags=["files"])
async def get_extras_top_level_folders() -> list[str]:
    """
    Returns top level folders in the extras directory
    \f
    :return: List of folders
    """
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    return read_dir(root_directory)


@ROUTER.get("/extras/{subdir}", tags=["files"])
async def get_subfolder_files_list(subdir: str) -> list[Path]:
    """
    Returns a list of files within a sub_folder. Directs users to use the /extras endpoint if folder not found

    :param subdir: The subdir to return the contents of
    :return: List of files within a subdir
    """
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    subdir_path = root_directory / subdir
    safe_check_filepath(root_directory, subdir_path)

    return read_dir(subdir_path)


@ROUTER.post("/extras/{instrument}/{filename}", tags=["files"])
async def upload_file_to_instrument_folder(instrument: str, filename: str, file: UploadFile) -> str:
    """
    Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    \f
    :param instrument: The instrument name
    :param filename: The name for the uploaded file
    :param file: The file contents
    :return: String with created filename
    """
    # the file path does not exist yet, so do checks with parent directory
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    file_directory = root_directory / instrument / filename
    safe_check_filepath(root_directory, file_directory)

    await write_file_from_remote(file, file_directory)

    return f"Successfully uploaded {filename}"
