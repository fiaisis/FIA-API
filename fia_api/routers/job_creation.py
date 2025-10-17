from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.job_maker import JobMaker
from fia_api.core.services.job import RerunJob, SimpleJob, get_experiment_number_for_job_id, job_maker
from fia_api.core.utility import get_packages

JobCreationRouter = APIRouter()
jwt_api_security = JWTAPIBearer()


@JobCreationRouter.post("/job/rerun", tags=["job creation"])
async def make_rerun_job(
    rerun_job: RerunJob,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    job_maker: Annotated[JobMaker, Depends(job_maker)],
) -> int:
    """
    Create a rerun job, returning the ID of the created job.
    \f
    :param rerun_job: The rerun job details including job ID, runner image, and script.
    :param credentials: httpAuthorizationCredentials  of the authenticated user.
    :param job_maker: dependency injected job maker instance used to create the rerun job.
    :return: The ID of the created job
    """
    user = get_user_from_token(credentials.credentials)
    experiment_number = get_experiment_number_for_job_id(rerun_job.job_id)
    # Forbidden if not staff, and experiment number not related to this user_number's experiment number
    if user.role != "staff":
        experiment_numbers = get_experiments_for_user_number(user.user_number)
        if experiment_number not in experiment_numbers:
            # If not staff this is not allowed
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    return job_maker.create_rerun_job(  # type: ignore # Despite returning int, mypy believes this returns any
        job_id=rerun_job.job_id,
        runner_image=rerun_job.runner_image,
        script=rerun_job.script,
        experiment_number=experiment_number,
    )


@JobCreationRouter.post("/job/simple", tags=["job creation"])
async def make_simple_job(
    simple_job: SimpleJob,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    job_maker: Annotated[JobMaker, Depends(job_maker)],
) -> int:
    """
    Create a simple job, returning the ID of the created job.
    \f
    :param simple_job: The simple job details including runner image and script.
    :param credentials: HTTPAuthorizationCredentials
    :param job_maker: Dependency injected job maker
    :return: The job id
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    return job_maker.create_simple_job(  # type: ignore # Despite returning int, mypy believes this returns any
        runner_image=simple_job.runner_image, script=simple_job.script, user_number=user.user_number
    )


@JobCreationRouter.get("/jobs/runners", tags=["job creation"])
async def get_mantid_runners(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> dict[str, str]:
    """Return a list of Mantid versions if user is authenticated."""
    user = get_user_from_token(credentials.credentials)

    if user.role is None or user.user_number is None:
        # Must be logged in to do this
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="User is not authorized to access this endpoint")

    data = get_packages(org="fiaisis", image_name="mantid")
    mantid_versions = {}
    for item in data:
        name = str(item.get("name", ""))
        tags = item.get("metadata", {}).get("container", {}).get("tags", [])
        if (tags == False): #if tags is an empty list
            continue
        else:
            mantid_versions[name] = str(tags[0])

    return mantid_versions
