"""Jobs API Router"""

import io
import json
import os
import zipfile
from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import (
    AuthError,
    NoFilesAddedError,
)
from fia_api.core.request_models import AutoreductionRequest, PartialJobUpdateRequest
from fia_api.core.responses import AutoreductionResponse, CountResponse, JobResponse, JobWithRunResponse
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    create_autoreduction_job,
    get_all_jobs,
    get_job_by_id,
    get_job_by_instrument,
    resolve_job_file_path,
    resolve_job_files,
    update_job_by_id,
)
from fia_api.core.session import get_db_session
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
    session: Annotated[Session, Depends(get_db_session)],
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
    :param session: The current session of the request
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
        session,
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
    session: Annotated[Session, Depends(get_db_session)],
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
    :param session: The current session of the request
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
        session,
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
    session: Annotated[Session, Depends(get_db_session)],
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
    return CountResponse(
        count=count_jobs_by_instrument(instrument, session, filters=json.loads(filters) if filters else None)
    )  # type: ignore


@JobsRouter.get("/job/{job_id}", tags=["jobs"])
async def get_job(
    job_id: int,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> JobWithRunResponse:
    """
    Retrieve a job with nested run data, by iD.
    \f
    :param job_id: the unique identifier of the job
    :param credentials: Dependency Injected credentials
    :param session: The current session of the request
    :return: JobWithRunsResponse object
    """
    user = get_user_from_token(credentials.credentials)
    job = (
        get_job_by_id(job_id, session)
        if user.role == "staff"
        else get_job_by_id(job_id, session, user_number=user.user_number)
    )
    return JobWithRunResponse.from_job(job)


@JobsRouter.patch("/job/{job_id}", tags=["jobs"])
async def update_job(
    job_id: int,
    job: PartialJobUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
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
        raise AuthError("User not authorised for this action")
    return JobResponse.from_job(update_job_by_id(job_id, job, session))


@JobsRouter.get("/jobs/count", tags=["jobs"])
async def count_all_jobs(
    session: Annotated[Session, Depends(get_db_session)],
    filters: Annotated[str | None, Query(description="json string of filters")] = None,
) -> CountResponse:
    """
    Count all jobs
    \f
    :param filters: json string of filters
    :return: CountResponse containing the count
    """
    return CountResponse(count=count_jobs(session, filters=json.loads(filters) if filters else None))


@JobsRouter.get("/job/{job_id}/filename/{filename}", tags=["jobs"])
async def download_file(
    job_id: int,
    filename: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> FileResponse:
    """
    Find a file in the CEPH_DIR and return it as a FileResponse.
    \f
    :param job_id: the unique identifier of the job.
    :param filename: the name of the file to find.
    :param credentials: Dependency injected HTTPAuthorizationCredentials.
    :param session: The current session of the request
    :return: FileResponse containing the file.
    """
    user = get_user_from_token(credentials.credentials)
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")

    filepath = resolve_job_file_path(
        job_id=job_id,
        filename=filename,
        user=user,
        ceph_dir=ceph_dir,
    )

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@JobsRouter.post("/job/download-zip", tags=["jobs"])
async def download_zip(
    job_files: dict[str, list[str]],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
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

    resolved_files, missing_files = resolve_job_files(job_files, user, ceph_dir)

    if not resolved_files:
        # signal which files were missing
        raise NoFilesAddedError(missing_files)

    zip_stream = io.BytesIO()
    with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zipf:
        for job_id, filename, filepath in resolved_files:
            arcname = f"{job_id}/{filename}"
            zipf.write(filepath, arcname=arcname)

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
    session: Annotated[Session, Depends(get_db_session)],
) -> AutoreductionResponse:
    """
    Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the autoreduction script
    \f
    :param job_request: The AutoreductionRequest
    :param credentials: Dependency injected HTTPAuthorizationCredentials.
    :param response: A Response object
    :param session: The current session of the request
    :return:  The AutoreductionResponse
    """
    user = get_user_from_token(credentials.credentials)
    if user.user_number != -1:  # API Key user has psuedo user number of -1
        raise AuthError(
            f"User number: {user.user_number} attempted to create autoreduction - \
                autoreduction only creatale via APIKey"
        )
    job = create_autoreduction_job(job_request, session)
    response.status_code = HTTPStatus.CREATED
    return AutoreductionResponse(job_id=job.id, script=job.script.script)  # type: ignore
