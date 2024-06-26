"""
Test cases for response objects
"""

import datetime
from unittest import mock

from fia_api.core.model import Instrument, Reduction, ReductionState, Run, Script
from fia_api.core.responses import (
    ReductionResponse,
    ReductionWithRunsResponse,
    RunResponse,
    ScriptResponse,
)

RUN = Run(
    filename="filename",
    experiment_number=123456,
    title="title",
    users="user 1, user 2",
    run_start=datetime.datetime(2000, 1, 1, 1, 1, 1, tzinfo=datetime.UTC),
    run_end=datetime.datetime(2000, 1, 1, 1, 2, 1, tzinfo=datetime.UTC),
    good_frames=1,
    raw_frames=2,
    instrument=Instrument(instrument_name="instrument name"),
)

SCRIPT = Script(script="print('foo')")

REDUCTION = Reduction(
    id=1,
    reduction_start=datetime.datetime(2000, 1, 1, 1, 1, 1, tzinfo=datetime.UTC),
    reduction_end=datetime.datetime(2000, 1, 1, 1, 5, 1, tzinfo=datetime.UTC),
    reduction_state=ReductionState.SUCCESSFUL,
    reduction_inputs={"ei": "auto"},
    reduction_outputs="some output",
    script=SCRIPT,
    stacktrace="some stacktrace",
    runs=[RUN],
)


def test_run_response_from_run():
    """
    Test run response can be built from run
    :return: None
    """
    response = RunResponse.from_run(RUN)
    assert response.filename == RUN.filename
    assert response.experiment_number == RUN.experiment_number
    assert response.title == RUN.title
    assert response.users == RUN.users
    assert response.run_start == RUN.run_start
    assert response.run_end == RUN.run_end
    assert response.good_frames == RUN.good_frames
    assert response.raw_frames == RUN.raw_frames
    assert response.instrument_name == RUN.instrument.instrument_name


@mock.patch(
    "fia_api.core.responses.ScriptResponse.from_script",
    return_value=ScriptResponse(value="print('foo')"),
)
def test_reduction_response_from_reduction(from_script):
    """
    Test that reduction response can be built from reduction
    :return: None
    """
    response = ReductionResponse.from_reduction(REDUCTION)
    from_script.assert_called_once_with(REDUCTION.script)
    assert not hasattr(response, "runs")
    assert response.id == REDUCTION.id
    assert response.reduction_state == REDUCTION.reduction_state
    assert response.script.value == REDUCTION.script.script
    assert response.reduction_start == REDUCTION.reduction_start
    assert response.reduction_end == REDUCTION.reduction_end
    assert response.reduction_inputs == REDUCTION.reduction_inputs
    assert response.reduction_outputs == REDUCTION.reduction_outputs
    assert response.reduction_status_message == REDUCTION.reduction_status_message
    assert response.stacktrace == REDUCTION.stacktrace


@mock.patch(
    "fia_api.core.responses.ScriptResponse.from_script",
    return_value=ScriptResponse(value="print('foo')"),
)
def test_reduction_with_runs_response_from_reduction(from_script):
    """
    Test reduction response can be built to include runs
    :return: None
    """
    response = ReductionWithRunsResponse.from_reduction(REDUCTION)
    from_script.assert_called_once_with(REDUCTION.script)
    assert response.id == REDUCTION.id
    assert response.reduction_state == REDUCTION.reduction_state
    assert response.script.value == REDUCTION.script.script
    assert response.reduction_start == REDUCTION.reduction_start
    assert response.reduction_end == REDUCTION.reduction_end
    assert response.reduction_inputs == REDUCTION.reduction_inputs
    assert response.reduction_outputs == REDUCTION.reduction_outputs
    assert response.reduction_status_message == REDUCTION.reduction_status_message
    assert isinstance(response.runs[0], RunResponse)


@mock.patch("fia_api.core.responses.filter_script_for_tokens", return_value=SCRIPT.script)
def test_script_attempts_to_filter_tokens(filter_script_for_tokens):
    """
    Test script response calls the util function when calling "from_script"
    :return: None
    """
    response: ScriptResponse = ScriptResponse.from_script(SCRIPT)
    assert response.value == SCRIPT.script
    filter_script_for_tokens.assert_called_once_with(SCRIPT.script)
