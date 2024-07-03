"""
Tests for reduction service
"""

from unittest.mock import Mock, patch

import pytest

from fia_api.core.exceptions import AuthenticationError, MissingRecordError
from fia_api.core.services.reduction import (
    count_reductions,
    count_reductions_by_instrument,
    get_all_reductions,
    get_reduction_by_id,
    get_reductions_by_instrument,
)


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.ReductionSpecification")
def test_get_reductions_by_instrument(mock_spec_class, mock_repo):
    """
    Test that get_reductions by instrument makes correct repo call
    :param mock_repo: Mocked Repo class
    :return: None
    """
    spec = mock_spec_class.return_value
    get_reductions_by_instrument("test", limit=5, offset=6)

    mock_repo.find.assert_called_once_with(spec.by_instrument("test", limit=5, offset=6))


@patch("fia_api.core.services.reduction._REPO")
def test_get_reduction_by_id_reduction_exists(mock_repo):
    """
    Test that correct repo call and return is made
    :param mock_repo: Mocked Repo
    :return:
    """
    expected_reduction = Mock()
    mock_repo.find_one.return_value = expected_reduction
    reduction = get_reduction_by_id(1)
    assert reduction == expected_reduction


@patch("fia_api.core.services.reduction._REPO")
def test_get_reduction_by_id_not_found_raises(mock_repo):
    """
    Test MissingRecordError raised when repo returns None
    :param mock_repo: Mocked Repo
    :return: None
    """
    mock_repo.find_one.return_value = None
    with pytest.raises(MissingRecordError):
        get_reduction_by_id(1)


@patch("fia_api.core.services.reduction._REPO")
def test_count_reductions(mock_repo):
    """
    Test count is called
    :return: None
    """
    count_reductions()
    mock_repo.count.assert_called_once()


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.ReductionSpecification")
def test_count_reductions_by_instrument(mock_spec_class, mock_repo):
    """
    Test count by instrument
    :param mock_repo: mock repo fixture
    :return: None
    """
    spec = mock_spec_class.return_value
    count_reductions_by_instrument("TEST")
    mock_repo.count.assert_called_once_with(spec.by_instrument("TEST"))


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
def test_get_reduction_by_id_for_user_no_experiments(mock_get_exp, mock_repo):
    """Test get_reduction_by_id when no experiments are permitted"""
    reduction = Mock()
    reduction.runs = [Mock(), Mock()]
    mock_repo.find_one.return_value = reduction
    mock_get_exp.return_value = []

    with pytest.raises(AuthenticationError):
        get_reduction_by_id(1, user_number=1234)


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
def test_get_reduction_by_id_for_user_with_experiments(mock_get_exp, mock_repo):
    """Test get_reduction_by_id_"""
    reduction = Mock()
    run = Mock()
    run.experiment_number = 1234
    reduction.runs = [run, Mock()]
    mock_repo.find_one.return_value = reduction
    mock_get_exp.return_value = [1234]

    assert get_reduction_by_id(1, 1234) == reduction


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.ReductionSpecification")
def test_get_all_reductions_without_user(mock_spec_class, mock_repo):
    """
    Test get_all_reductions without a user number
    """
    spec = mock_spec_class.return_value
    get_all_reductions(limit=10, offset=5, order_by="reduction_end", order_direction="asc")
    spec.all.assert_called_once_with(limit=10, offset=5, order_by="reduction_end", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.ReductionSpecification")
@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
def test_get_all_reductions_with_user_having_access(mock_get_experiments, mock_spec_class, mock_repo):
    """
    Test get_all_reductions with a user number and the user has access to experiments
    """
    mock_get_experiments.return_value = [123, 456]
    spec = mock_spec_class.return_value
    get_all_reductions(user_number=1234, limit=5, offset=0, order_by="reduction_start", order_direction="desc")
    mock_get_experiments.assert_called_once_with(1234)
    spec.by_experiment_numbers.assert_called_once_with(
        [123, 456], limit=5, offset=0, order_by="reduction_start", order_direction="desc"
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())


@patch("fia_api.core.services.reduction._REPO")
@patch("fia_api.core.services.reduction.ReductionSpecification")
@patch("fia_api.core.services.reduction.get_experiments_for_user_number")
def test_get_all_reductions_with_user_no_access(mock_get_experiments, mock_spec_class, mock_repo):
    """
    Test get_all_reductions with a user number but no access to any experiments
    """
    mock_repo.find.return_value = []
    mock_get_experiments.return_value = []
    spec = mock_spec_class.return_value
    reductions = get_all_reductions(user_number=9876)
    mock_get_experiments.assert_called_once_with(9876)
    spec.by_experiment_numbers.assert_called_once_with(
        [], order_by="reduction_start", order_direction="desc", limit=0, offset=0
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())
    assert reductions == []
