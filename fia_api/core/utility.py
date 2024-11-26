"""Collection of utility functions"""

import os
import functools
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from typing import Any, TypeVar, cast

import requests
from fastapi import HTTPException

from fia_api.core.exceptions import UnsafePathError

FuncT = TypeVar("FuncT", bound=Callable[[str], Any])

GITHUB_PACKAGE_TOKEN = os.environ.get("GITHUB_PACKAGE_TOKEN", "shh")


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


def get_packages(org: str, image_name: str) -> Any:
    """Helper function for getting package versions from GitHub."""
    response = requests.get(
        f"https://api.github.com/orgs/{org}/packages/container/{image_name}/versions",
        headers={"Authorization": f"Bearer {GITHUB_PACKAGE_TOKEN}"},
        timeout=10,
    )
    if response.status_code != HTTPStatus.OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"GitHub API request failed with status code {response.status_code}: {response.text}",
        )
    return response.json()
