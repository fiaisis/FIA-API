"""API Level Exception Handlers."""

from starlette.requests import Request
from starlette.responses import JSONResponse


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
