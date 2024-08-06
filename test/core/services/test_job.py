"""
Tests for job service
"""

from unittest.mock import Mock, patch

import pytest

from fia_api.core.exceptions import AuthenticationError, MissingRecordError
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    get_all_jobs,
    get_job_by_id,
    get_job_by_instrument,
)


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_jobs_by_instrument(mock_spec_class, mock_repo):
    """
    Test that get_jobs by instrument makes correct repo call
    :param mock_repo: Mocked Repo class
    :return: None
    """
    spec = mock_spec_class.return_value
    get_job_by_instrument("test", limit=5, offset=6)

    mock_repo.find.assert_called_once_with(spec.by_instrument("test", limit=5, offset=6))


@patch("fia_api.core.services.job._REPO")
def test_get_job_by_id_job_exists(mock_repo):
    """
    Test that correct repo call and return is made
    :param mock_repo: Mocked Repo
    :return:
    """
    expected_job = Mock()
    mock_repo.find_one.return_value = expected_job
    job = get_job_by_id(1)
    assert job == expected_job


@patch("fia_api.core.services.job._REPO")
def test_get_job_by_id_not_found_raises(mock_repo):
    """
    Test MissingRecordError raised when repo returns None
    :param mock_repo: Mocked Repo
    :return: None
    """
    mock_repo.find_one.return_value = None
    with pytest.raises(MissingRecordError):
        get_job_by_id(1)


@patch("fia_api.core.services.job._REPO")
def test_count_jobs(mock_repo):
    """
    Test count is called
    :return: None
    """
    count_jobs()
    mock_repo.count.assert_called_once()


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_count_jobs_by_instrument(mock_spec_class, mock_repo):
    """
    Test count by instrument
    :param mock_repo: mock repo fixture
    :return: None
    """
    spec = mock_spec_class.return_value
    count_jobs_by_instrument("TEST")
    mock_repo.count.assert_called_once_with(spec.by_instrument("TEST"))


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_no_experiments(mock_get_exp, mock_repo):
    """Test get_job_by_id when no experiments are permitted"""
    job = Mock()
    job.owner = Mock()
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = []

    with pytest.raises(AuthenticationError):
        get_job_by_id(1, user_number=1234)


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_with_experiments(mock_get_exp, mock_repo):
    """Test get_job_by_id_"""
    job = Mock()
    job.owner.experiment_number = 1234
    job.runs = [job, Mock()]
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = [1234]

    assert get_job_by_id(1, 1234) == job


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_with_user_number(mock_get_exp, mock_repo):
    """Test get_job_by_id_"""
    job = Mock()
    job.owner.user_number = 1234
    job.runs = [job, Mock()]
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = [1234]

    assert get_job_by_id(1, 1234) == job


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_without_user(mock_spec_class, mock_repo):
    """
    Test get_all_jobs without a user number
    """
    spec = mock_spec_class.return_value
    get_all_jobs(limit=10, offset=5, order_by="end", order_direction="asc")
    spec.all.assert_called_once_with(limit=10, offset=5, order_by="end", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_all_jobs_with_user_having_access(mock_get_experiments, mock_spec_class, mock_repo):
    """
    Test get_all_jobs with a user number and the user has access to experiments
    """
    mock_get_experiments.return_value = [123, 456]
    spec = mock_spec_class.return_value
    get_all_jobs(user_number=1234, limit=5, offset=0, order_by="start", order_direction="desc")
    mock_get_experiments.assert_called_once_with(1234)
    spec.by_experiment_numbers.assert_called_once_with(
        [123, 456], limit=5, offset=0, order_by="start", order_direction="desc"
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_all_jobs_with_user_no_access(mock_get_experiments, mock_spec_class, mock_repo):
    """
    Test get_all_jobs with a user number but no access to any experiments
    """
    mock_repo.find.return_value = []
    mock_get_experiments.return_value = []
    spec = mock_spec_class.return_value
    jobs = get_all_jobs(user_number=9876)
    mock_get_experiments.assert_called_once_with(9876)
    spec.by_experiment_numbers.assert_called_once_with([], order_by="start", order_direction="desc", limit=0, offset=0)
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())
    assert jobs == []
