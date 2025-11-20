import os
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import BadRequestError, UserPermissionError
from fia_api.core.utility import (
    find_file_experiment_number,
    find_file_instrument,
    find_file_user_number,
    request_path_check,
)

FindFileRouter = APIRouter(prefix="/find_file", tags=["files"])

jwt_api_security = JWTAPIBearer()


@FindFileRouter.get("/instrument/{instrument}/experiment_number/{experiment_number}", tags=["find_files"])
async def find_file_get_instrument(
    instrument: str,
    experiment_number: int,
    filename: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> str:
    """
    Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.
    \f
    :param instrument: Instrument the file belongs to.
    :param experiment_number: Experiment number the file belongs to.
    :param filename: Filename to find.
    :return: The relative path to the file in the CEPH_DIR env var.
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        experiment_numbers = get_experiments_for_user_number(user.user_number)
        if experiment_number not in experiment_numbers:
            # If not staff this is not allowed
            raise UserPermissionError("Experiment number not found in user's experiments")
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
    path = find_file_instrument(
        ceph_dir=ceph_dir, instrument=instrument, experiment_number=experiment_number, filename=filename
    )
    if path is None:
        raise BadRequestError("Path is none")
    return str(request_path_check(path=path, base_dir=ceph_dir))


@FindFileRouter.get("/generic/experiment_number/{experiment_number}", tags=["find_files"])
async def find_file_generic_experiment_number(
    experiment_number: int,
    filename: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> str:
    """
    Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.
    \f
    :param experiment_number: Experiment number the file belongs to.
    :param filename: Filename to find
    :return: The relative path to the file in the CEPH_DIR env var.
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        experiment_numbers = get_experiments_for_user_number(user.user_number)
        if experiment_number not in experiment_numbers:
            # If not staff this is not allowed
            raise UserPermissionError(status_code=HTTPStatus.FORBIDDEN)
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
    path = find_file_experiment_number(ceph_dir=ceph_dir, experiment_number=experiment_number, filename=filename)
    if path is None:
        raise BadRequestError("Could not find file")
    return str(request_path_check(path=path, base_dir=ceph_dir))


@FindFileRouter.get("/generic/user_number/{user_number}", tags=["find_files"])
async def find_file_generic_user_number(
    user_number: int, filename: str, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)]
) -> str:
    """
    Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.
    \f
    :param user_number: Experiment number the file belongs to.
    :param filename: Filename to find
    :return: The relative path to the file in the CEPH_DIR env var.
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff" and user_number != user.user_number:
        # If not staff and not the user of the file this is not allowed
        raise UserPermissionError("User is not staff, and/or experiment does not belong to User")
    ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
    path = find_file_user_number(ceph_dir=ceph_dir, user_number=user_number, filename=filename)
    if path is None:
        raise BadRequestError("Could not find file")
    return str(request_path_check(path, base_dir=ceph_dir))
