"""Test cases for experiments module."""

from http import HTTPStatus
from unittest.mock import Mock, patch

from fia_api.core.auth.experiments import AUTH_EXPERIMENTS_CACHE_TTL_SECONDS, get_experiments_for_user_number


@patch("fia_api.core.auth.experiments.cache_set_json")
@patch("fia_api.core.auth.experiments.cache_get_json")
@patch("fia_api.core.auth.experiments.requests.get")
def test_get_experiments_for_user_number_bad_status_returns_empty_list(mock_get, mock_cache_get, mock_cache_set):
    """Test when non OK status returned."""
    mock_cache_get.return_value = None
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = HTTPStatus.NOT_FOUND

    assert get_experiments_for_user_number(1234) == []
    mock_cache_set.assert_not_called()


@patch("fia_api.core.auth.experiments.cache_set_json")
@patch("fia_api.core.auth.experiments.cache_get_json")
@patch("fia_api.core.auth.experiments.requests.get")
def test_get_experiments_for_user_number_returns_experiment_numbers(mock_get, mock_cache_get, mock_cache_set):
    """Test when OK status returned."""
    mock_cache_get.return_value = None
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = [1, 2, 3, 4]
    assert get_experiments_for_user_number(1234) == [1, 2, 3, 4]
    mock_cache_set.assert_called_once_with(
        "fia_api:auth:experiments:1234",
        [1, 2, 3, 4],
        AUTH_EXPERIMENTS_CACHE_TTL_SECONDS,
    )


@patch("fia_api.core.auth.experiments.cache_get_json")
@patch("fia_api.core.auth.experiments.requests.get")
def test_get_experiments_for_user_number_uses_cache(mock_get, mock_cache_get):
    """Test that cached experiments are returned and no request is made."""
    mock_cache_get.return_value = [10, 20]

    assert get_experiments_for_user_number(1234) == [10, 20]
    mock_get.assert_not_called()
