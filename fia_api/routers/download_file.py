import os
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.utility import request_path_check

ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
download_file_router = APIRouter(prefix="find_file", tags=["download_files"])
jwt_api_security = JWTAPIBearer()


@download_file_router.get("/{filepath}", tags=["download_files"])
async def find_file_get_instrument(
    filepath: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> FileResponse:
    """
    Find a file in the CEPH_DIR and return it as a FileResponse.
    :param filepath: Location of file to find.
    :param credentials: The JWT token for authentication.
    :return: The file response.
    """
    user = get_user_from_token(credentials.credentials)

    if user.role != "staff":
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)

    full_filepath = Path(ceph_dir) / filepath

    if full_filepath is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    request_path_check(filepath, base_dir=ceph_dir)

    return FileResponse(
        path=full_filepath,
        filename=Path.name(full_filepath),
        media_type="application/octet-stream",
    )
