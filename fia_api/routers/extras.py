import os
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.file_ops import read_dir, write_file_from_remote
from fia_api.core.utility import safe_check_filepath

ExtrasRouter = APIRouter(prefix="/extras", tags=["files"])

jwt_api_security = JWTAPIBearer()

InstrumentString = Literal[
    "alf",
    "argus",
    "chipir",
    "chronus",
    "crisp",
    "emu",
    "enginx",
    "gem",
    "hifi",
    "hrpd",
    "imat",
    "ines",
    "inter",
    "iris",
    "larmor",
    "let",
    "loq",
    "maps",
    "mari",
    "merlin",
    "musr",
    "nimrod",
    "offspec",
    "osiris",
    "pearl",
    "polaris",
    "polref",
    "sandals",
    "sans2d",
    "surf",
    "sxd",
    "tosca",
    "vesuvio",
    "wish",
    "zoom",
    "test",
    "test",
]


@ExtrasRouter.get("/", tags=["files"])
async def get_extras_top_level_folders(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> list[str]:
    """
    Returns top level folders in the extras directory
    \f
    :return: List of folders
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    safe_check_filepath(root_directory, root_directory)
    return read_dir(root_directory)


@ExtrasRouter.get("/{subdir}", tags=["files"])
async def get_subfolder_files_list(
    subdir: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> list[str]:
    """
    Returns a list of files within a sub_folder. Directs users to use the /extras endpoint if folder not found

    :param subdir: The subdir to return the contents of
    :return: List of files within a subdir
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    subdir_path = root_directory / subdir
    safe_check_filepath(subdir_path, root_directory)

    return read_dir(subdir_path)


@ExtrasRouter.post("/{instrument}/{filename}", tags=["files"])
async def upload_file_to_instrument_folder(
    instrument: InstrumentString,
    filename: str,
    file: UploadFile,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> str:
    """
    Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    \f
    :param instrument: The instrument name
    :param filename: The name for the uploaded file
    :param file: The file contents
    :return: String with created filename
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    # the file path does not exist yet, so do checks with parent directory
    root_directory = Path(os.environ.get("EXTRAS_DIRECTORY", "/extras"))
    file_directory = root_directory / instrument / filename
    safe_check_filepath(file_directory, root_directory)

    await write_file_from_remote(file, file_directory)

    return f"Successfully uploaded {filename}"


