"""Cache behavior tests for jobs endpoints."""

from http import HTTPStatus
from unittest.mock import patch

from starlette.testclient import TestClient

from fia_api.fia_api import app

from .constants import STAFF_HEADER

client = TestClient(app)


@patch("fia_api.routers.jobs.JOB_LIST_CACHE_TTL_SECONDS", 15)
@patch("fia_api.core.auth.tokens.requests.post")
@patch("fia_api.routers.jobs.cache_set_json")
@patch("fia_api.routers.jobs.get_all_jobs")
@patch("fia_api.routers.jobs.cache_get_json")
def test_jobs_list_cache_hit_returns_cached_payload(
    mock_cache_get,
    mock_get_all_jobs,
    mock_cache_set,
    mock_post,
):
    cached_payload = [
        {
            "id": 1,
            "start": None,
            "end": None,
            "state": "NOT_STARTED",
            "status_message": None,
            "inputs": {},
            "outputs": None,
            "stacktrace": None,
            "script": None,
            "runner_image": None,
            "type": "JobType.AUTOREDUCTION",
        }
    ]
    mock_cache_get.return_value = cached_payload
    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get("/jobs?limit=1", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_payload
    mock_get_all_jobs.assert_not_called()
    mock_cache_set.assert_not_called()


@patch("fia_api.routers.jobs.JOB_COUNT_CACHE_TTL_SECONDS", 15)
@patch("fia_api.routers.jobs.count_jobs")
@patch("fia_api.routers.jobs.cache_get_json")
def test_jobs_count_cache_hit_returns_cached_payload(mock_cache_get, mock_count_jobs):
    cached_payload = {"count": 42}
    mock_cache_get.return_value = cached_payload

    response = client.get("/jobs/count")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_payload
    mock_count_jobs.assert_not_called()


@patch("fia_api.routers.jobs.JOB_COUNT_CACHE_TTL_SECONDS", 15)
@patch("fia_api.routers.jobs.count_jobs_by_instrument")
@patch("fia_api.routers.jobs.cache_get_json")
def test_jobs_count_by_instrument_cache_hit_returns_cached_payload(mock_cache_get, mock_count_jobs):
    cached_payload = {"count": 7}
    mock_cache_get.return_value = cached_payload

    response = client.get("/instrument/TEST/jobs/count")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == cached_payload
    mock_count_jobs.assert_not_called()
