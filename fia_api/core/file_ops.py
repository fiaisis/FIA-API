from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path

import anyio
from fastapi import HTTPException, UploadFile


def read_dir(path: Path) -> list[str]:
    """
    Read the names of each file in the given path
    :param path: The path to the directory to get the filenames of
    :return: A list of paths in the given param path
    """
    try:
        return os.listdir(path)
    except Exception as err:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"There was an error returning the files {err}, {type(err)}",
        ) from err


async def write_file_from_remote(remote_file: UploadFile, local_file: Path) -> None:
    """
    Write the contents of the remote_file from called to the local path given.
    """
    try:
        contents = await remote_file.read()
        path = anyio.Path(local_file)
        await path.write_bytes(contents)
    except PermissionError as err:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f"Permissions denied for the instrument folder {err}",
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file {err}, {type(err)}",
        ) from err
