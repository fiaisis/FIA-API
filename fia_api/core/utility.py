"""Collection of utility functions"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast

from fia_api.core.exceptions import UnsafePathError

FuncT = TypeVar("FuncT", bound=Callable[[str], Any])


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
