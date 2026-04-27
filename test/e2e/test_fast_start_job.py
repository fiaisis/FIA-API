from http import HTTPStatus
from unittest.mock import MagicMock, patch

from starlette.testclient import TestClient

from fia_api.core.auth.tokens import User
from fia_api.fia_api import app
from test.e2e.constants import STAFF_HEADER, USER_HEADER


@patch("fia_api.core.job_maker.BlockingConnection")
@patch("requests.post")
def test_fast_start_job_lifecycle(mock_post, _, faker):
    client = TestClient(app)
    """
    Test the lifecycle of a fast start job:
    1. Creation via API (calls external service)
    2. Retrieval (filtering)
    3. Status patching via API Key
    """

    headers = USER_HEADER

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_post.return_value = mock_response

    response = client.post("/job/fast-start", json={"script": "print('hello')"}, headers=headers)
    assert response.status_code == HTTPStatus.OK
    job_id = response.json()

    # Verify external API call
    # requests.post is called by auth (token checkToken check) and then by job_maker (LLSP call)
    # searches for the creation call
    found_llsp_call = False
    for calls in mock_post.call_args_list:
        if calls.kwargs.get("json") == {"script": "print('hello')"} and calls.kwargs.get("headers") == {
            "Authorization": "Bearer shh"
        }:
            found_llsp_call = True
            break
    assert found_llsp_call

    # Default should EXCLUDE fast start jobs
    response = client.get("/jobs/count", headers=headers)
    assert response.status_code == HTTPStatus.OK
    default_count = response.json()["count"]

    # Explicitly INCLUDE fast start jobs
    response = client.get("/jobs/count?include_fast_start_jobs=true", headers=headers)
    assert response.status_code == HTTPStatus.OK
    included_count = response.json()["count"]

    # So included_count should be > default_count (since we just created one)
    assert included_count > default_count

    response = client.patch(f"/job/{job_id}", json={"state": "SUCCESSFUL"}, headers=headers)

    assert response.status_code in (401, 403)

    # Try to patch with API Key (user -1)
    with patch("fia_api.routers.jobs.get_user_from_token") as mock_get_user:
        mock_user = User(user_number=-1, role="staff")
        mock_get_user.return_value = mock_user

        response = client.patch(
            f"/job/{job_id}", json={"state": "SUCCESSFUL"}, headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()["state"] == "SUCCESSFUL"


@patch("requests.post")
def test_get_only_fast_start_jobs(mock_post):
    client = TestClient(app)
    """
    Test retrieving ONLY fast start jobs.
    """

    mock_post.return_value.status_code = HTTPStatus.OK

    response = client.get(
        '/jobs?include_fast_start_jobs=true&filters={"job_type_in": ["FAST_START"]}',
        headers=STAFF_HEADER,
    )
    assert response.status_code == HTTPStatus.OK

    jobs = response.json()
    assert len(jobs) > 0, "Expected at least one fast start job in seeded db"

    for job in jobs:
        assert job["type"] == "JobType.FAST_START"

    response_count = client.get(
        '/jobs/count?include_fast_start_jobs=true&filters={"job_type_in": ["FAST_START"]}',
        headers=STAFF_HEADER,
    )
    assert response_count.status_code == HTTPStatus.OK
    assert response_count.json()["count"] == len(jobs)
