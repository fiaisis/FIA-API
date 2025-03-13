import json
from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.request_models import PartialJobUpdateRequest
from fia_api.core.responses import CountResponse, JobResponse, JobWithRunResponse
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    get_all_jobs,
    get_job_by_id,
    get_job_by_instrument,
    update_job_by_id,
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
    return CountResponse(count=count_jobs_by_instrument(instrument, filters=json.loads(filters) if filters else None))


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
