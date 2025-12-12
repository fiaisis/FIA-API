from http import HTTPStatus
from unittest.mock import patch

from test.e2e.constants import USER_HEADER
from test.e2e.test_core import client


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners(mock_post):
    """Test endpoint contains all the Mantid runners."""
    mock_post.return_value.status_code = HTTPStatus.OK
    expected_runners = {
        "sha256:7cb55a70ee776614189af8569b1d7e99dc57cdf5b704b628dab71dce2e22319d": "6.8.0",
        "sha256:e44992cc15f8efcd565fd05065fbc80a7c7a5eab86f9cf1091c690179b85cd59": "6.9.0",
        "sha256:6e5f2d070bb67742f354948d68f837a740874d230714eaa476d35ab6ad56caec": "6.9.1",
        "sha256:33ec46f0b3e36e5ddb83eeaf32389846c6e05358253c67a25819161693740f62": "6.10.0",
        "sha256:7f7c8deab696d2d567f412c924dac36cbfc52794cf0dd6b043d75c8a83acf6b7": "6.11.0",
        "sha256:a30765d8750ff6bb6cfe5950b3fa6fbea43e559cd16bc3338f11b21e11e63a7e": "6.12.0",
        "sha256:f3f169428aa62a340bd9a1382e4db8f0fb9b69a41d6edac1543e9a7accb5148a": "6.12.1",
        "sha256:0676ed97dcd784dd802138e244f283d71a0f6712863345eb20143b6bcf8fb129": "6.13.0",
        "sha256:3d5085cd4d8a9d0b87cb7ac69f9a929cce7ab0cfb474808d7fb87bb7040acc54": "6.13.1",
    }
    response = client.get("/jobs/runners", headers=USER_HEADER)
    assert response.status_code == HTTPStatus.OK
    for runner in expected_runners:
        assert runner in response.json()


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners_no_api_key(mock_post):
    """Test endpoint returns forbidden if no API key supplied."""
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/jobs/runners")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@patch("fia_api.core.auth.tokens.requests.post")
def test_get_mantid_runners_bad_jwt(mock_post):
    """Test endpoint returns forbidden if bad JWT supplied."""
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/jobs/runners", headers={"Authorization": "foo"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
