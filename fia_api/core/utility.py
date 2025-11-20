"""Collection of utility functions"""

from __future__ import annotations

import functools
import hashlib
import os
from collections.abc import Callable
from contextlib import suppress
from http import HTTPStatus
from pathlib import Path
from typing import Any, TypeVar, cast

import requests

from fia_api.core.exceptions import UnsafePathError, InvalidPathError, BadRequestError, GithubAPIRequestError

FuncT = TypeVar("FuncT", bound=Callable[[str], Any])

GITHUB_PACKAGE_TOKEN = os.environ.get("GITHUB_PACKAGE_TOKEN", "shh")


def forbid_path_characters(func: FuncT) -> FuncT:
    """Decorator that prevents path characters {/, ., \\} from a functions args by raising UnsafePathError"""

    @functools.wraps(func)
    def wrapper(arg: str) -> Any:
        if any(char in arg for char in (".", "/", "\\")):
            raise UnsafePathError(f"Potentially unsafe path was requested: {arg}")
        return func(arg)

    return cast("FuncT", wrapper)


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
            raise InvalidPathError("Invalid path being accessed.")
    except FileNotFoundError as err:
        # pathlibs is_file and is_dir do not work on non existent paths
        if "." in filepath.name:
            safe_check_filepath(filepath.parent, base_path)
        else:
            raise InvalidPathError(err)


def get_packages(org: str, image_name: str) -> Any:
    """Helper function for getting package versions from GitHub."""
    response = requests.get(
        f"https://api.github.com/orgs/{org}/packages/container/{image_name}/versions",
        headers={"Authorization": f"Bearer {GITHUB_PACKAGE_TOKEN}"},
        timeout=10,
    )
    if response.status_code != HTTPStatus.OK:
        raise GithubAPIRequestError(
            f"GitHub API request failed with status code {response.status_code}: {response.text}",
        )
    return response.json()


def safe_check_filepath_plotting(filepath: Path, base_path: str) -> None:
    """
    Check to ensure the path does contain the base path and that it does not resolve to some other directory
    :param filepath: the filepath to check
    :param base_path: base path to check against
    :return:
    """
    filepath.resolve(strict=True)
    if not filepath.is_relative_to(base_path):
        raise InvalidPathError("Invalid path being accessed.")


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
        raise InvalidPathError("Invalid path being accessed.") from None

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
        raise BadRequestError("Invalid or nonexistent path")
    # Remove the base_dir
    if path.is_relative_to(base_dir):
        path = path.relative_to(base_dir)
    return path


def hash_script(script: str) -> str:
    """
    Given a script, return the sha512 hash of the script
    :param script: the script to hash
    :return: The script hash
    """
    return hashlib.sha512(script.encode()).hexdigest()
