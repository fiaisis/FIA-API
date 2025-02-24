import pytest
from fastapi import HTTPException

from fia_api.core.specifications.filters import (
    ExperimentNumberAfterFilter,
    ExperimentNumberBeforeFilter,
    ExperimentNumberInFilter,
    FilenameFilter,
    InstrumentInFilter,
    JobEndAfterFilter,
    JobEndBeforeFilter,
    JobStartAfterFilter,
    JobStartBeforeFilter,
    JobStateFilter,
    RunEndAfterFilter,
    RunEndBeforeFilter,
    RunStartAfterFilter,
    RunStartBeforeFilter,
    TitleFilter,
    get_filter,
)


def test_get_filter_invalid_key():
    """
    Test the behavior of get_filter function when provided with an invalid key.
    Ensure it raises an HTTPException.
    """
    with pytest.raises(HTTPException):
        get_filter("invalid_key", "test")


@pytest.mark.parametrize(
    ("key", "value", "expected_class"),
    [
        ("instrument_in", "value1", InstrumentInFilter),
        ("job_state_in", "value2", JobStateFilter),
        ("experiment_number_in", "value4", ExperimentNumberInFilter),
        ("title", "value5", TitleFilter),
        ("filename", "value6", FilenameFilter),
        ("job_start_before", "value7", JobStartBeforeFilter),
        ("job_start_after", "value8", JobStartAfterFilter),
        ("run_start_before", "value9", RunStartBeforeFilter),
        ("run_start_after", "value10", RunStartAfterFilter),
        ("job_end_before", "value11", JobEndBeforeFilter),
        ("job_end_after", "value12", JobEndAfterFilter),
        ("run_end_before", "value13", RunEndBeforeFilter),
        ("run_end_after", "value14", RunEndAfterFilter),
        ("experiment_number_before", "value15", ExperimentNumberBeforeFilter),
        ("experiment_number_after", "value16", ExperimentNumberAfterFilter),
    ],
)
def test_get_filter(key, value, expected_class):
    """Test filter factory"""
    result = get_filter(key, value)
    assert isinstance(result, expected_class)
    assert result.value == value
