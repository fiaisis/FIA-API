import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from fia_api.core.auth.tokens import JWTAPIBearer

ceph_dir = os.environ.get("CEPH_DIR", "/ceph")
download_file_router = APIRouter(prefix=f"/{ceph_dir}", tags=["download_files"])
jwt_api_security = JWTAPIBearer()


@download_file_router.get("/{filepath}", tags=["download_files"])
async def find_file_get_instrument(
    filepath: str,
) -> FileResponse:
    """
    Find a file in the CEPH_DIR and return it as a FileResponse.
    :param filepath: Location of file to find.
    :return: The file response.
    """
    full_file_path = Path(ceph_dir) / filepath
    return FileResponse(
        path=full_file_path,
        filename=Path.name(full_file_path),
        media_type="application/octet-stream",
    )
