"""API Level Exception Handlers."""

import logging

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


async def missing_record_handler(_: Request, __: Exception) -> JSONResponse:
    """
    Automatically return a 404 when a MissingRecordError is raised
    :param _:
    :param __:
    :return: JSONResponse with 404
    """
    return JSONResponse(
        status_code=404,
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


async def validation_exception_hander(request: Request, exc: RequestValidationError):
    """
    Provide a more verbose error message for validation errors
    :param request: The request object
    :param exc: The validation Exception
    :return: JSONResponse
    """
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 422, "message": exc_str}
    return JSONResponse(content=content, status_code=422)
