"""Module containing user experiment fetching."""

import os
from http import HTTPStatus
from typing import Any

import requests

from fia_api.core.auth import AUTH_URL
from fia_api.core.cache import cache_get_json, cache_set_json

API_KEY = os.environ.get("AUTH_API_KEY", "shh")
AUTH_EXPERIMENTS_CACHE_TTL_SECONDS = int(os.environ.get("AUTH_EXPERIMENTS_CACHE_TTL_SECONDS", "120"))


def get_experiments_for_user_number(user_number: int) -> list[int]:
    """Given a user number fetch and return the experiment (RB) numbers for
    that user.

    :param user_number: The user number to fetch for
    :return: List of ints (experiment numbers)
    """
    cache_key = f"fia_api:auth:experiments:{user_number}"
    cached = cache_get_json(cache_key)
    if isinstance(cached, list):
        return cached

    response = requests.get(
        f"{AUTH_URL}/experiments?user_number={user_number}", timeout=30, headers={"Authorization": f"Bearer {API_KEY}"}
    )
    if response.status_code == HTTPStatus.OK:
        experiments: list[Any] = response.json()
        cache_set_json(cache_key, experiments, AUTH_EXPERIMENTS_CACHE_TTL_SECONDS)
        return experiments
    return []
