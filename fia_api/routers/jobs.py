"""Jobs API Router"""

import io
import json
import os
import zipfile
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import NoFilesAddedError
from fia_api.core.models import JobType
from fia_api.core.request_models import AutoreductionRequest, PartialJobUpdateRequest
from fia_api.core.responses import AutoreductionResponse, CountResponse, JobResponse, JobWithRunResponse
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    create_autoreduction_job,
    get_all_jobs,
    get_job_by_id,
    get_job_by_instrument,
    update_job_by_id,
)
from fia_api.core.utility import (
    find_file_experiment_number,
    find_file_instrument,
    find_file_user_number,
)

JobsRouter = APIRouter(tags=["jobs"])
jwt_api_security = JWTAPIBearer()

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


@JobsRouter.get("/jobs", tags=["jobs"])
async def get_jobs(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_run: bool = False,
    filters: Annotated[str | None, Query(description="json string of filters")] = None,
    as_user: bool = False,
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
    :param filters: json string of filters
    :param as_user: bool
    :return: List of JobResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    filters = json.loads(filters) if filters else None

    if as_user:
        user_number = user.user_number
    elif user.role == "staff":
        user_number = None
    else:
        user_number = user.user_number

    jobs = get_all_jobs(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        user_number=user_number,
        filters=filters,
    )

    if include_run:
        return [JobWithRunResponse.from_job(j) for j in jobs]
    return [JobResponse.from_job(j) for j in jobs]


@JobsRouter.get("/instrument/{instrument}/jobs", tags=["jobs"])
async def get_jobs_by_instrument(
    instrument: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_run: bool = False,
    filters: Annotated[str | None, Query(description="json string of filters")] = None,
    as_user: bool = False,
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
    :param filters: json string of filters
    :param as_user: bool
    :return: List of JobResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    filters = json.loads(filters) if filters else None

    instrument = instrument.upper()

    if as_user:
        user_number = user.user_number
    elif user.role == "staff":
        user_number = None
    else:
        user_number = user.user_number

    jobs = get_job_by_instrument(
        instrument,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        user_number=user_number,
        filters=filters,
    )

    if include_run:
        return [JobWithRunResponse.from_job(j) for j in jobs]
    return [JobResponse.from_job(j) for j in jobs]


@JobsRouter.get("/instrument/{instrument}/jobs/count", tags=["jobs"])
async def count_jobs_for_instrument(
    instrument: str,
    filters: Annotated[str | None, Query(description="json string of filters")] = None,
) -> CountResponse:
    """
    Count jobs for a given instrument.
    \f
    :param instrument: the name of the instrument
    :param filters: json string of filters
    :return: CountResponse containing the count
    """
    instrument = instrument.upper()
    return CountResponse(count=count_jobs_by_instrument(instrument, filters=json.loads(filters) if filters else None))  # type: ignore


@JobsRouter.get("/job/{job_id}", tags=["jobs"])
async def get_job(
    job_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)]
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


@JobsRouter.patch("/job/{job_id}", tags=["jobs"])
async def update_job(
    job_id: int,
    job: PartialJobUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> JobResponse:
    """
    Safely update the job of the given id with the new details provided. The update is safe as it prevents
    retroactive changes of values that should never change
    \f
    :param job_id: the unique identifier of the job
    :param job: the job to update with
    :param credentials: Dependency injected HTTPAuthorizationCredentials
    :return: JobResponse
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    return JobResponse.from_job(update_job_by_id(job_id, job))


@JobsRouter.get("/jobs/count", tags=["jobs"])
async def count_all_jobs(
    filters: Annotated[str | None, Query(description="json string of filters")] = None,
) -> CountResponse:
    """
    Count all jobs
    \f
    :param filters: json string of filters
    :return: CountResponse containing the count
    """
    return CountResponse(count=count_jobs(filters=json.loads(filters) if filters else None))


@JobsRouter.get("/job/{job_id}/filename/{filename}", tags=["jobs"])
async def download_file(
    job_id: int,
    filename: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> FileResponse:
    """
    Find a file in the CEPH_DIR and return it as a FileResponse.
    \f
    :param job_id: the unique identifier of the job.
    :param filename: the name of the file to find.
    :param credentials: Dependency injected HTTPAuthorizationCredentials.
    :return: FileResponse containing the file.
    """
    user = get_user_from_token(credentials.credentials)
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
    job = get_job_by_id(job_id) if user.role == "staff" else get_job_by_id(job_id, user_number=user.user_number)

    if job.owner is None:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Job has no owner.")

    if job.job_type != JobType.SIMPLE:
        if job.owner.experiment_number is None:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Experiment number not found in scenario where it should be expected.",
            )
        if job.instrument is None:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Instrument not found in scenario where it should be expected.",
            )
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
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="User number not found in scenario where it should be expected.",
            )
        filepath = find_file_user_number(
            ceph_dir=ceph_dir,
            user_number=int(job.owner.user_number),
            filename=filename,
        )

    if filepath is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="File not found.")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@JobsRouter.post("/job/download-zip", tags=["jobs"])
async def download_zip(
    job_files: dict[str, list[str]],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> StreamingResponse:
    """
    Zips and returns a set of files given job IDs and filenames.
    \f
    :param job_files: Dict mapping job_id (int) to list of filenames.
    :param credentials: Dependency injected HTTPAuthorizationCredentials.
    :return: StreamingResponse containing the ZIP file.
    """
    user = get_user_from_token(credentials.credentials)
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")

    zip_stream = io.BytesIO()
    missing_files: list[str] = []
    no_file_added = True

    with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zipf:
        for job_id_str, filenames in job_files.items():
            job_id = int(job_id_str)
            job = get_job_by_id(job_id) if user.role == "staff" else get_job_by_id(job_id, user_number=user.user_number)

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
                    filepath = find_file_experiment_number(ceph_dir, int(job.owner.experiment_number), filename)
                elif job.owner.user_number:
                    filepath = find_file_user_number(ceph_dir, int(job.owner.user_number), filename)
                else:
                    filepath = None

                if filepath and Path(filepath).is_file():
                    arcname = f"{job_id}/{filename}"
                    zipf.write(filepath, arcname=arcname)
                    no_file_added = False
                else:
                    missing_files.append(f"{job_id}/{filename}")

    if no_file_added:
        raise NoFilesAddedError(missing_files)

    zip_stream.seek(0)
    resp = StreamingResponse(zip_stream, media_type="application/zip")
    resp.headers["content-disposition"] = "attachment; filename=reduction_files.zip"

    if missing_files:
        resp.headers["x-missing-files-count"] = str(len(missing_files))
        resp.headers["x-missing-files"] = ";".join(missing_files)

    return resp


@JobsRouter.post("/job/autoreduction")
async def create_autoreduction(
    job_request: AutoreductionRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    response: Response,
) -> AutoreductionResponse:
    """
    Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the autoreduction script
    \f
    :param job_request: The AutoreductionRequest
    :param credentials: Dependency injected HTTPAuthorizationCredentials.
    :return:  The AutoreductionResponse
    """
    user = get_user_from_token(credentials.credentials)
    if user.user_number != -1:  # API Key user has psuedo user number of -1
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    job = create_autoreduction_job(job_request)
    response.status_code = HTTPStatus.CREATED
    return AutoreductionResponse(job_id=job.id, script=job.script.script)  # type: ignore
