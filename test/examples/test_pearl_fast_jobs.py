import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to sys.path to import the script
sys.path.append(str(Path(__file__).parent.parent.parent))

from examples.job_scripts.pearl_fast_jobs import PearlFastStart, main
from fia_api.core.models import State


@pytest.fixture(scope="session")
def get_fast_start():
    fia_url = "http://fia-api"
    auth_url = "http://auth-api"
    username = "test_user"
    password = "test_pass"  # noqa S105
    output_dir = "./test_output"
    return PearlFastStart(fia_url, auth_url, username, password, output_dir)


@patch("examples.job_scripts.pearl_fast_jobs.requests.post")
def test_authenticate_success(mock_post, get_fast_start):
    automation = get_fast_start
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


@patch("examples.job_scripts.pearl_fast_jobs.requests.post")
def test_authenticate_success_string_token(mock_post, get_fast_start):
    """Auth APIs that return a bare string token (not a dict) are also handled."""
    automation = get_fast_start
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = "valid_token"
    mock_post.return_value = mock_response

    automation.authenticate()
    assert automation.token == "valid_token"  # noqa: S105


@patch("examples.job_scripts.pearl_fast_jobs.requests.post")
def test_authenticate_no_token_raises_error(mock_post, get_fast_start):
    automation = get_fast_start
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}  # Missing token
    mock_post.return_value = mock_response

    with pytest.raises(ValueError, match="No token found in login response"):
        automation.authenticate()


@patch("examples.job_scripts.pearl_fast_jobs.requests.post")
def test_submit_job_success(mock_post, get_fast_start):
    automation = get_fast_start
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = 12345
    mock_post.return_value = mock_response

    job_id = automation.submit_job("print('hello')")
    expected_job_id = 12345
    assert job_id == expected_job_id
    mock_post.assert_called_once()


@patch("examples.job_scripts.pearl_fast_jobs.requests.get")
@patch("examples.job_scripts.pearl_fast_jobs.time.sleep", return_value=None)
def test_monitor_job_success(mock_sleep, mock_get, get_fast_start):
    automation = get_fast_start
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


@pytest.mark.parametrize("state", [State.ERROR.value, State.UNSUCCESSFUL.value])
@patch("examples.job_scripts.pearl_fast_jobs.requests.get")
def test_monitor_job_failure_raises_error(mock_get, get_fast_start, state):
    automation = get_fast_start
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"state": state, "status_message": "Something went wrong"}
    mock_get.return_value = mock_response

    with pytest.raises(RuntimeError, match="Something went wrong"):
        automation.monitor_job(12345)


@patch("examples.job_scripts.pearl_fast_jobs.requests.get")
@patch("examples.job_scripts.pearl_fast_jobs.Path.open", new_callable=unittest.mock.mock_open)
def test_download_results(mock_open, mock_get, get_fast_start):
    automation = get_fast_start
    automation.token = "valid_token"  # noqa S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"data1", b"data2"]
    mock_get.return_value = mock_response

    automation.download_results(12345, "file1.csv, file2.csv, ")  # Added empty entry to test filter
    expected_call_count = 2

    assert mock_get.call_count == expected_call_count
    assert mock_open.call_count == expected_call_count


def test_download_results_no_outputs(get_fast_start):
    automation = get_fast_start
    with patch("examples.job_scripts.pearl_fast_jobs.logger.warning") as mock_log:
        automation.download_results(12345, None)
        mock_log.assert_called_with("No outputs found for job 12345")


@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.authenticate")
@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.submit_job")
@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.monitor_job")
@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.download_results")
def test_run_success(mock_dl, mock_mon, mock_sub, mock_auth, get_fast_start):
    automation = get_fast_start
    mock_sub.return_value = 1
    mock_mon.return_value = {"outputs": "out"}

    automation.run()

    mock_auth.assert_called_once()
    mock_sub.assert_called_once()
    mock_mon.assert_called_once_with(1)
    mock_dl.assert_called_once_with(1, "out")


@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.authenticate", side_effect=Exception("Auth fail"))
@patch("examples.job_scripts.pearl_fast_jobs.sys.exit")
def test_run_failure(mock_exit: MagicMock, mock_auth: MagicMock, get_fast_start: PearlFastStart) -> None:
    automation = get_fast_start
    automation.run()
    mock_exit.assert_called_once_with(1)


@patch("examples.job_scripts.pearl_fast_jobs.sys.argv", ["pearl_fast_jobs.py", "--username", "u", "--password", "p"])
@patch("examples.job_scripts.pearl_fast_jobs.PearlFastStart.run")
def test_main_success(mock_run: MagicMock) -> None:
    main()
    mock_run.assert_called_once()


@patch("examples.job_scripts.pearl_fast_jobs.sys.argv", ["pearl_fast_jobs.py", "--username", "", "--password", ""])
@patch("examples.job_scripts.pearl_fast_jobs.sys.exit", side_effect=SystemExit)
def test_main_no_creds_exits(mock_exit: MagicMock) -> None:
    with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
        main()
    mock_exit.assert_called_once_with(1)


@patch("examples.job_scripts.pearl_fast_jobs.requests.get")
@patch("examples.job_scripts.pearl_fast_jobs.Path.open", new_callable=unittest.mock.mock_open)
def test_download_results_list_input(mock_open: MagicMock, mock_get: MagicMock, get_fast_start: PearlFastStart) -> None:
    automation = get_fast_start
    automation.token = "valid_token"  # noqa: S105
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"data"]
    mock_get.return_value = mock_response

    automation.download_results(12345, ["file1.csv"])
    assert mock_get.call_count == 1
    assert mock_open.call_count == 1


def test_main_entry_point() -> None:
    # Run the script as a subprocess to cover the if __name__ == "__main__": block
    # We provide invalid args so it exits quickly
    result = subprocess.run(
        [sys.executable, "-m", "examples.job_scripts.pearl_fast_jobs", "--username", ""],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Username and password must be provided" in result.stderr
