"""Test cases for experiments module"""

from http import HTTPStatus
from unittest.mock import Mock, patch

from fia_api.core.auth.experiments import get_experiments_for_user_number


@patch("fia_api.core.auth.experiments.requests.get")
def test_get_experiments_for_user_number_bad_status_returns_empty_list(mock_get):
    """Test when non OK status returned"""
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = HTTPStatus.NOT_FOUND

    assert get_experiments_for_user_number(1234) == []


@patch("fia_api.core.auth.experiments.requests.get")
def test_get_experiments_for_user_number_returns_experiment_numbers(mock_get):
    """Test when OK status returned"""
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = [1, 2, 3, 4]
    assert get_experiments_for_user_number(1234) == [1, 2, 3, 4]
