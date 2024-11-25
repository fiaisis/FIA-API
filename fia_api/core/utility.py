"""Collection of utility functions"""

import functools
import logging
import os
import re
import sys
from collections.abc import Callable
from contextlib import suppress
from http import HTTPStatus
from pathlib import Path
from typing import Any, TypeVar, cast

from fastapi import HTTPException
from starlette.requests import Request

from fia_api.core.exceptions import UnsafePathError

FuncT = TypeVar("FuncT", bound=Callable[[str], Any])

stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("Starting Plotting Service")
CEPH_DIR = os.environ.get("CEPH_DIR", "/ceph")
logger.info("Setting ceph directory to %s", CEPH_DIR)


def forbid_path_characters(func: FuncT) -> FuncT:
    """Decorator that prevents path characters {/, ., \\} from a functions args by raising UnsafePathError"""

    @functools.wraps(func)
    def wrapper(arg: str) -> Any:
        if any(char in arg for char in (".", "/", "\\")):
            raise UnsafePathError(f"Potentially unsafe path was requested: {arg}")
        return func(arg)

    return cast(FuncT, wrapper)


def filter_script_for_tokens(script: str) -> str:
    """
    Filters out lines that contain tokens i.e. 'ghp_' and 'network.github.api_token' from the script,
    by cutting that line.
    :param script: The script to filter
    :return: The filtered script
    """
    script_list = script.splitlines()
    filtered_script_list = [
        line for line in script_list if "ghp_" not in line and "network.github.api_token" not in line
    ]

    return "\n".join(filtered_script_list)


def safe_check_filepath(filepath: Path, base_path: Path) -> None:
    """
    Check to ensure the path does contain the base path and that it does not resolve to some other directory
    :param filepath: the filepath to check
    :param base_path: base path to check against
    :return:
    """
    try:
        filepath.resolve(strict=True)
        if not filepath.is_relative_to(base_path):
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed.")
    except FileNotFoundError as err:
        # pathlibs is_file and is_dir do not work on non existent paths
        if "." in filepath.name:
            safe_check_filepath(filepath.parent, base_path)
        else:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed and file not found."
            ) from err


def safe_check_filepath_plotting(filepath: Path, base_path: str) -> None:
    """
    Check to ensure the path does contain the base path and that it does not resolve to some other directory
    :param filepath: the filepath to check
    :param base_path: base path to check against
    :return:
    """
    filepath.resolve(strict=True)
    if not filepath.is_relative_to(base_path):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed.")


def find_file_instrument(ceph_dir: str, instrument: str, experiment_number: int, filename: str) -> Path | None:
    """
    Find a file likely made by automated reduction of an experiment number
    :param ceph_dir: base path of the filename path
    :param instrument: name of the instrument to find the file in
    :param experiment_number: experiment number of the file
    :param filename: name of the file to find
    :return: path to the filename or None
    """
    # Run normal check
    basic_path = Path(ceph_dir) / f"{instrument.upper()}/RBNumber/RB{experiment_number}/autoreduced/{filename}"

    # Do a check as we are handling user entered data here
    with suppress(OSError):
        safe_check_filepath_plotting(filepath=basic_path, base_path=ceph_dir)

    if basic_path.exists():
        return basic_path

    # Attempt to find file in autoreduced folder
    autoreduced_folder = Path(ceph_dir) / f"{instrument.upper()}/RBNumber/RB{experiment_number}/autoreduced"
    return _safe_find_file_in_dir(dir_path=autoreduced_folder, base_path=ceph_dir, filename=filename)


def find_file_experiment_number(ceph_dir: str, experiment_number: int, filename: str) -> Path | None:
    """
    Find the file for the given user_number
    :param ceph_dir: base path of the path
    :param experiment_number: experiment_number of the user who made the file and dir path
    :param filename: filename to find
    :return: Full path to the filename or None
    """
    dir_path = Path(ceph_dir) / f"GENERIC/autoreduce/ExperimentNumbers/{experiment_number}/"
    return _safe_find_file_in_dir(dir_path=dir_path, base_path=ceph_dir, filename=filename)


def find_file_user_number(ceph_dir: str, user_number: int, filename: str) -> Path | None:
    """
    Find the file for the given user_number
    :param ceph_dir: base path of the path
    :param user_number: user number of the user who made the file and dir path
    :param filename: filename to find
    :return: Full path to the filename or None
    """
    dir_path = Path(ceph_dir) / f"GENERIC/autoreduce/UserNumbers/{user_number}/"
    return _safe_find_file_in_dir(dir_path=dir_path, base_path=ceph_dir, filename=filename)


def find_experiment_number(request: Request) -> int:
    """
    Find the experiment number from a request
    :param request: Request to be used to get the experiment number
    :return: Experiment number in the request
    """
    if request.url.path.startswith("/text"):
        return int(request.url.path.split("/")[-1])
    if request.url.path.startswith("/find_file"):
        url_parts = request.url.path.split("/")
        try:
            experiment_number_index = url_parts.index("experiment_number")
            return int(url_parts[experiment_number_index + 1])
        except (ValueError, IndexError):
            logger.warning(
                f"The requested path {request.url.path} does not include an experiment number. "
                f"Permissions cannot be checked"
            )
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Request missing experiment number") from None
    match = re.search(r"%2FRB(\d+)%2F", request.url.query)
    if match is not None:
        return int(match.group(1))

    logger.warning(
        f"The requested nexus metadata path {request.url.path} does not include an experiment number. "
        f"Permissions cannot be checked"
    )
    raise HTTPException(HTTPStatus.BAD_REQUEST, "Request missing experiment number")


def _safe_find_file_in_dir(dir_path: Path, base_path: str, filename: str) -> Path | None:
    """
    Check that the directory path is safe and then search for filename in that directory and sub directories
    :param dir_path: Path to check is safe and search in side of
    :param base_path: the base directory of the path often just the /ceph dir on runners
    :param filename: filename to find
    :return: Path to the file or None
    """
    # Do a check as we are handling user entered data here
    try:
        safe_check_filepath_plotting(filepath=dir_path, base_path=base_path)
    except OSError:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed.") from None

    if dir_path.exists():
        found_paths = list(dir_path.rglob(filename))
        if len(found_paths) > 0 and found_paths[0].exists():
            return found_paths[0]

    return None


def request_path_check(path: Path, base_dir: str) -> Path:
    """
    Check if the path is not None, and remove the base dir from the path.
    :param path: Path to check
    :param base_dir: Base dir to remove if present
    :return: Path without the base_dir
    """
    if path is None:
        logger.error("Could not find the file requested.")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    # Remove CEPH_DIR
    if path.is_relative_to(base_dir):
        path = path.relative_to(base_dir)
    return path
