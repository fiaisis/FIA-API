"""
Test cases for response objects
"""

import copy
import datetime
from unittest import mock

from db.data_models import Instrument, Job, JobOwner, JobType, Run, Script, State

from fia_api.core.responses import (
    JobResponse,
    JobWithRunResponse,
    RunResponse,
    ScriptResponse,
)

OWNER = JobOwner(user_number=1111, experiment_number=2222)

RUN = Run(
    filename="filename",
    title="title",
    users="user 1, user 2",
    run_start=datetime.datetime(2000, 1, 1, 1, 1, 1, tzinfo=datetime.UTC),
    run_end=datetime.datetime(2000, 1, 1, 1, 2, 1, tzinfo=datetime.UTC),
    good_frames=1,
    raw_frames=2,
    instrument=Instrument(instrument_name="instrument name"),
    owner=OWNER,
)

SCRIPT = Script(script="print('foo')")

JOB = Job(
    id=1,
    start=datetime.datetime(2000, 1, 1, 1, 1, 1, tzinfo=datetime.UTC),
    end=datetime.datetime(2000, 1, 1, 1, 5, 1, tzinfo=datetime.UTC),
    state=State.SUCCESSFUL,
    inputs={"ei": "auto"},
    outputs="some output",
    script=SCRIPT,
    stacktrace="some stacktrace",
    run=RUN,
    job_type=JobType.AUTOREDUCTION,
)


def test_run_response_from_run():
    """
    Test run response can be built from run
    :return: None
    """
    response = RunResponse.from_run(RUN)
    assert response.filename == RUN.filename
    assert response.experiment_number == RUN.owner.experiment_number
    assert response.title == RUN.title
    assert response.users == RUN.users
    assert response.run_start == RUN.run_start
    assert response.run_end == RUN.run_end
    assert response.good_frames == RUN.good_frames
    assert response.raw_frames == RUN.raw_frames
    assert response.instrument_name == RUN.instrument.instrument_name


def test_run_response_from_run_when_no_owner():
    """
    Test run response can be built from run without owner
    :return: None
    """
    local_run = copy.deepcopy(RUN)
    local_run.owner = None
    response = RunResponse.from_run(local_run)
    assert response.filename == RUN.filename
    assert response.experiment_number is None
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
def test_job_response_from_job(from_script):
    """
    Test that job response can be built from job
    :return: None
    """
    response = JobResponse.from_job(JOB)
    from_script.assert_called_once_with(JOB.script)
    assert not hasattr(response, "runs")
    assert response.id == JOB.id
    assert response.state == JOB.state
    assert response.script.value == JOB.script.script
    assert response.start == JOB.start
    assert response.end == JOB.end
    assert response.inputs == JOB.inputs
    assert response.outputs == JOB.outputs
    assert response.status_message == JOB.status_message
    assert response.stacktrace == JOB.stacktrace
    assert response.type == str(JOB.job_type)


@mock.patch(
    "fia_api.core.responses.ScriptResponse.from_script",
    return_value=ScriptResponse(value="print('foo')"),
)
def test_job_with_runs_response_from_job(from_script):
    """
    Test job response can be built to include runs
    :return: None
    """
    response = JobWithRunResponse.from_job(JOB)
    from_script.assert_called_once_with(JOB.script)
    assert response.id == JOB.id
    assert response.state == JOB.state
    assert response.script.value == JOB.script.script
    assert response.start == JOB.start
    assert response.end == JOB.end
    assert response.inputs == JOB.inputs
    assert response.outputs == JOB.outputs
    assert response.status_message == JOB.status_message
    assert response.run == RunResponse.from_run(JOB.run)
    assert response.type == str(JOB.job_type)


@mock.patch("fia_api.core.responses.filter_script_for_tokens", return_value=SCRIPT.script)
def test_script_attempts_to_filter_tokens(filter_script_for_tokens):
    """
    Test script response calls the util function when calling "from_script"
    :return: None
    """
    response: ScriptResponse = ScriptResponse.from_script(SCRIPT)
    assert response.value == SCRIPT.script
    filter_script_for_tokens.assert_called_once_with(SCRIPT.script)
