import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to sys.path to import the script
sys.path.append(str(Path(__file__).parent.parent.parent))

from fia_api.core.models import State
from fia_api.scripts.pearl_automation import PearlAutomation


@pytest.fixture(scope="session")
def get_automation():
    fia_url = "http://fia-api"
    auth_url = "http://auth-api"
    username = "test_user"
    password = "test_pass"  # noqa S105
    output_dir = "./test_output"
    return PearlAutomation(fia_url, auth_url, username, password, output_dir)


@patch("fia_api.scripts.pearl_automation.requests.post")
def test_authenticate_success(mock_post, get_automation):
    automation = get_automation
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "valid_token"}
    mock_post.return_value = mock_response

    automation.authenticate()
    assert automation.token == "valid_token"  # noqa S105
    mock_post.assert_called_once_with(
        f"{automation.auth_url}/login",
        json={"username": automation.username, "password": automation.password},
        timeout=30,
    )

@patch("fia_api.scripts.pearl_automation.requests.post")
def test_authenticate_failed_raises_error(mock_post, get_automation):
    automation = get_automation
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"token": "invalid_token"}
    mock_post.return_value = mock_response

    with pytest.raises(Exception):
        automation.authenticate()
    


@patch("fia_api.scripts.pearl_automation.requests.get")
def test_get_runner_image_success(mock_get, get_automation):
    automation = get_automation
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"6.8.0": "sha1", "6.9.0": "sha2"}
    mock_get.return_value = mock_response

    runner = automation.get_runner_image()
    assert runner == "6.9.0"
    mock_get.assert_called_once()


@patch("fia_api.scripts.pearl_automation.requests.post")
def test_submit_job_success(mock_post, get_automation):
    automation = get_automation
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = 12345
    mock_post.return_value = mock_response

    job_id = automation.submit_job("print('hello')", "6.9.0")
    expected_job_id = 12345
    assert job_id == expected_job_id
    mock_post.assert_called_once()


@patch("fia_api.scripts.pearl_automation.requests.get")
@patch("fia_api.scripts.pearl_automation.time.sleep", return_value=None)
def test_monitor_job_success(mock_sleep, mock_get, get_automation):
    automation = get_automation
    automation.token = "valid_token"  # noqa S105

    # Mock responses for polling: 1st NOT_STARTED, 2nd SUCCESSFUL
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {"state": State.NOT_STARTED.value}

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {"state": State.SUCCESSFUL.value, "outputs": "file1.csv,file2.csv"}

    mock_get.side_effect = [mock_response_1, mock_response_2]

    job_data = automation.monitor_job(12345, poll_interval=0)
    assert job_data["state"] == State.SUCCESSFUL.value
    expected_call_count = 2
    assert mock_get.call_count == expected_call_count


@patch("fia_api.scripts.pearl_automation.requests.get")
@patch("fia_api.scripts.pearl_automation.Path.open", new_callable=unittest.mock.mock_open)
def test_download_results(mock_open, mock_get, get_automation):
    automation = get_automation
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"data1", b"data2"]
    mock_get.return_value = mock_response

    automation.download_results(12345, "file1.csv, file2.csv")
    expected_call_count = 2

    assert mock_get.call_count == expected_call_count
    assert mock_open.call_count == expected_call_count
