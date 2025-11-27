from __future__ import annotations

import os
from pathlib import Path

import anyio
from fastapi import UploadFile

from fia_api.core.exceptions import AuthError, ReadDirError, UploadFileError


def read_dir(path: Path) -> list[str]:
    """
    Read the names of each file in the given path
    :param path: The path to the directory to get the filenames of
    :return: A list of paths in the given param path
    """
    try:
        return os.listdir(path)  # noqa: PTH208
    except Exception as err:
        raise ReadDirError(err) from err


async def write_file_from_remote(remote_file: UploadFile, local_file: Path) -> None:
    """Write the contents of the remote_file from called to the local path given."""
    try:
        contents = await remote_file.read()
        path = anyio.Path(local_file)
        await path.write_bytes(contents)
    except PermissionError as err:
        raise AuthError(err) from err
    except Exception as err:
        raise UploadFileError(err) from err
