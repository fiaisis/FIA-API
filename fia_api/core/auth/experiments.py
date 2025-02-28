"""Module containing user experiment fetching"""

import os
from http import HTTPStatus
from typing import Any

import requests

from fia_api.core.auth import AUTH_URL

API_KEY = os.environ.get("AUTH_API_KEY", "shh")


def get_experiments_for_user_number(user_number: int) -> list[int]:
    """
    Given a user number fetch and return the experiment (RB) numbers for that user
    :param user_number: The user number to fetch for
    :return: List of ints (experiment numbers)
    """
    response = requests.get(
        f"{AUTH_URL}/experiments?user_number={user_number}", timeout=30, headers={"Authorization": f"Bearer {API_KEY}"}
    )
    if response.status_code == HTTPStatus.OK:
        experiments: list[Any] = response.json()
        return experiments
    return []
