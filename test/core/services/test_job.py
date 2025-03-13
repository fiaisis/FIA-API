"""Tests for job service"""

from unittest.mock import Mock, patch

import faker.generator
import pytest
from db.data_models import State

from fia_api.core.exceptions import AuthenticationError, MissingRecordError
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    get_all_jobs,
    get_experiment_number_for_job_id,
    get_job_by_id,
    get_job_by_instrument,
    update_job_by_id,
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

    mock_repo.find.assert_called_once_with(spec.by_instruments(["test"], limit=5, offset=6))


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
    count_jobs_by_instrument("TEST", filters={})
    mock_repo.count.assert_called_once_with(spec.by_instruments(["TEST"]))


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
    """Test get_all_jobs without a user number"""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=10, offset=5, order_by="end", order_direction="asc")
    spec.all.assert_called_once_with(limit=10, offset=5, order_by="end", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_all_jobs_with_user_having_access(mock_get_experiments, mock_spec_class, mock_repo):
    """Test get_all_jobs with a user number and the user has access to experiments"""
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
    """Test get_all_jobs with a user number but no access to any experiments"""
    mock_repo.find.return_value = []
    mock_get_experiments.return_value = []
    spec = mock_spec_class.return_value
    jobs = get_all_jobs(user_number=9876)
    mock_get_experiments.assert_called_once_with(9876)
    spec.by_experiment_numbers.assert_called_once_with(
        [], order_by="start", order_direction="desc", limit=100, offset=0
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())
    assert jobs == []


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_experiment_number_from_job_id(mock_spec_class, mock_repo):
    job_id = faker.generator.random.randint(1, 1000)

    get_experiment_number_for_job_id(job_id)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class().by_id())


@patch("fia_api.core.services.job._REPO")
def test_get_experiment_number_from_job_id_expect_raise(mock_repo):
    job_id = faker.generator.random.randint(1, 1000)
    mock_repo.find_one.return_value = None

    with patch("fia_api.core.services.job.JobSpecification"), pytest.raises(ValueError):  # noqa: PT011
        get_experiment_number_for_job_id(job_id)


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_order_by_run_start_desc(mock_spec_class, mock_repo):
    """Test get_all_jobs with order_by 'run_start' in descending order."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0, order_by="run_start", order_direction="desc")
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="run_start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_order_by_run_start_asc(mock_spec_class, mock_repo):
    """Test get_all_jobs with order_by 'run_start' in ascending order."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0, order_by="run_start", order_direction="asc")
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="run_start", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_default_order_by_start(mock_spec_class, mock_repo):
    """
    Test get_all_jobs without specifying a different order_by, per the function signature it should order by 'start'.
    """
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0)
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_with_pagination(mock_spec_class, mock_repo):
    """Test get_all_jobs with custom pagination (limit and offset)."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=15, offset=30)
    spec.all.assert_called_once_with(limit=15, offset=30, order_by="start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id(mock_spec_class, mock_repo):
    """Test update_job_by_id with valid job data."""
    job_id = 1
    job_data = Mock()  # This represents the JobResponse object
    job_data.state = State.SUCCESSFUL
    job_data.end = "2023-10-10T10:00:00"
    job_data.status_message = "Job completed successfully"
    job_data.outputs = {"output_key": "output_value"}
    job_data.stacktrace = None

    original_job = Mock()
    mock_repo.find_one.return_value = original_job

    update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    assert original_job.state == State.SUCCESSFUL
    assert original_job.end == "2023-10-10T10:00:00"
    assert original_job.status_message == "Job completed successfully"
    assert original_job.outputs == {"output_key": "output_value"}
    assert original_job.stacktrace is None
    mock_repo.update_one.assert_called_once_with(original_job)


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id_invalid_job_id(mock_spec_class, mock_repo):
    """Test update_job_by_id when the job ID does not exist."""
    job_id = 999
    job_data = Mock()
    mock_repo.find_one.return_value = None  # Simulate job not found

    with pytest.raises(MissingRecordError):
        update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    mock_repo.update_one.assert_not_called()


@patch("fia_api.core.services.job._REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id_never_updates_certain_fields(mock_spec_class, mock_repo):
    """Test update_job_by_id ensuring certain fields are never updated"""
    job_id = 2
    job_data = Mock()
    job_data.state = State.NOT_STARTED
    job_data.start = "2023-10-09T12:00:01"
    job_data.status_message = "Job is running"
    job_data.input = None  # input should never be updated
    job_data.stacktrace = "Some stacktrace info"

    original_job = Mock()
    original_job.start = "2023-10-09T12:00:00"
    original_job.input = {"output_key": "previous_output"}

    mock_repo.find_one.return_value = original_job

    update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    assert original_job.state == State.NOT_STARTED
    assert original_job.start == "2023-10-09T12:00:01"
    assert original_job.status_message == "Job is running"
    assert original_job.input == {"output_key": "previous_output"}  # Ensure this remains unchanged
    assert original_job.stacktrace == "Some stacktrace info"
    mock_repo.update_one.assert_called_once_with(original_job)
