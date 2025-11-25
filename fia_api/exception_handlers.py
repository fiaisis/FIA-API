"""API Level Exception Handlers."""

import logging
from http import HTTPStatus

from fastapi import Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from fia_api.core.exceptions import NoFilesAddedError

logger = logging.getLogger(__name__)


async def missing_record_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return a 404 when a MissingRecordError is raised
    :param _:
    :param __:
    :return: JSONResponse with 404
    """
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"message": "Resource not found"},
    )


async def bad_job_request_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return a 400 when a BadJobRequest is raised
    :param _:
    :param __:
    :return: JSONResponse with 400
    """
    return JSONResponse(
        status_code=400,
        content={"message": "The job request was malformed and could not be processed"},
    )


async def missing_script_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return a 404 when the script could not be found locally or remote
    :param _:
    :param __:
    :return:  JSONResponse with 404
    """
    return JSONResponse(
        status_code=404,
        content={
            "message": "The script could not be found locally or on remote, it is likely the script does not exist"
        },
    )


async def unsafe_path_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return 400 status code when an unsafe path error is raised
    :param _:
    :param __:
    :return:
    """
    return JSONResponse(
        status_code=400,
        content={"message": "The given request contains bad characters"},
    )


async def authentication_error_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatatically return a 403 when an authentication error is raised
    :param _:
    :param __:
    :return:
    """
    return JSONResponse(status_code=403, content={"message": "Forbidden"})


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Provide a more verbose error message for validation errors
    :param request: The request object
    :param exc: The validation Exception
    :return: JSONResponse
    """
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str}
    return JSONResponse(content=content, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)


async def no_files_added_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for NoFilesAddedError."""
    assert isinstance(
        exc, NoFilesAddedError
    )  # This assert can be removed and the type hint updated, if this PR gets merged: https://github.com/encode/starlette/pull/2403
    return JSONResponse(
        status_code=404,
        content={
            "detail": "None of the requested files could be found.",
            "missing_files_count": len(exc.missing_files),
            "missing_files": exc.missing_files,
        },
        headers={
            "x-missing-files-count": str(len(exc.missing_files)),
            "x-missing-files": ";".join(exc.missing_files),
        },
    )


async def read_dir_err_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for file_ops.read_dir()"""

    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=f"There was an error returning the files {exc}"
    )


async def upload_permissions_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for file_ops.write_file_from_remote() permissions error"""

    return JSONResponse(status_code=HTTPStatus.FORBIDDEN, content=f"Permissions denied for the instrument folder {exc}")


async def upload_file_err_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for file_ops.write_file_from_remote()"""
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=f"There was an error uploading the file {exc}"
    )


async def invalid_path_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for utility.safe_check_filepath"""

    return JSONResponse(
        status_code=HTTPStatus.FORBIDDEN, content=f"Invalid path being access and file not found, {exc}"
    )


async def github_api_request_handler(_: Response, __: Exception) -> JSONResponse:
    """Handler for GithubAPI requests that fail"""

    return JSONResponse(status_code=HTTPStatus.FAILED_DEPENDENCY, content="Github API request failed ")


async def bad_request_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for bad requests"""

    return JSONResponse(status_code=HTTPStatus.BAD_REQUEST, content=f"A bad request was made, {exc}")


async def invalid_token_handler(_: Request, __: Exception) -> JSONResponse:
    """Handler for invalid/expired tokens or invalid API keys"""

    return JSONResponse(status_code=HTTPStatus.FORBIDDEN, content="Invalid or expired token, or invalid API key")


async def service_unavailable_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handler for health.health_router.get"""

    return JSONResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, content=f"Service Unavailable, {exc}")


async def user_permission_err_handler(_: Request, __: Exception) -> JSONResponse:
    """Handler for user permissions errors"""

    return JSONResponse(status_code=HTTPStatus.FORBIDDEN, content="This operation is only allowed for staff")


async def job_owner_err_handler(_: Request, __: Exception) -> JSONResponse:
    """Handler for JobOwnerErr"""

    return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content="Job has no owner")


async def data_integrity_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return a 500 when a DataIntegrityError is raised
    :param _:
    :param __:
    :return: JSONResponse with 500
    """
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"message": "Record missing experiment, instrument, or user number"},
    )
