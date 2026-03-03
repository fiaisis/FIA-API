import unittest
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import os
import sys

# Add the project root to sys.path to import the script
sys.path.append(str(Path(__file__).parent.parent.parent))

from fia_api.scripts.pearl_automation import PearlAutomation
from fia_api.core.models import State

@pytest.fixture(autouse=True)
def setup():
    self.fia_url = "http://fia-api"
    self.auth_url = "http://auth-api"
    self.username = "test_user"
    self.password = "test_pass"
    self.output_dir = "./test_output"
    self.automation = PearlAutomation(
        self.fia_url, self.auth_url, self.username, self.password, self.output_dir
    )

@patch("fia_api.scripts.pearl_automation.requests.post")
def test_authenticate_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "valid_token"}
    mock_post.return_value = mock_response

    self.automation.authenticate()
    self.assertEqual(self.automation.token, "valid_token")
    mock_post.assert_called_once_with(
        f"{self.auth_url}/login",
        json={"username": self.username, "password": self.password},
        timeout=30
    )

@patch("fia_api.scripts.pearl_automation.requests.get")
def test_get_runner_image_success(mock_get):
    self.automation.token = "valid_token"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"6.8.0": "sha1", "6.9.0": "sha2"}
    mock_get.return_value = mock_response

    runner = self.automation.get_runner_image()
    self.assertEqual(runner, "6.9.0")
    mock_get.assert_called_once()

@patch("fia_api.scripts.pearl_automation.requests.post")
def test_submit_job_success(mock_post):
    self.automation.token = "valid_token"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = 12345
    mock_post.return_value = mock_response

    job_id = self.automation.submit_job("print('hello')", "6.9.0")
    self.assertEqual(job_id, 12345)
    mock_post.assert_called_once()

@patch("fia_api.scripts.pearl_automation.requests.get")
@patch("fia_api.scripts.pearl_automation.time.sleep", return_value=None)
def test_monitor_job_success(mock_sleep, mock_get):
    self.automation.token = "valid_token"
    
    # Mock responses for polling: 1st NOT_STARTED, 2nd SUCCESSFUL
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {"state": State.NOT_STARTED.value}
    
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {"state": State.SUCCESSFUL.value, "outputs": "file1.csv,file2.csv"}
    
    mock_get.side_effect = [mock_response_1, mock_response_2]

    job_data = self.automation.monitor_job(12345, poll_interval=0)
    self.assertEqual(job_data["state"], State.SUCCESSFUL.value)
    self.assertEqual(mock_get.call_count, 2)

@patch("fia_api.scripts.pearl_automation.requests.get")
@patch("fia_api.scripts.pearl_automation.open", new_callable=unittest.mock.mock_open)
def test_download_results(mock_open, mock_get):
    self.automation.token = "valid_token"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"data1", b"data2"]
    mock_get.return_value = mock_response

    self.automation.download_results(12345, "file1.csv, file2.csv")
    
    self.assertEqual(mock_get.call_count, 2)
    self.assertEqual(mock_open.call_count, 2)
