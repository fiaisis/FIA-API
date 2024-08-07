"""
responses module contains api response definitions
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from db.data_models import Job, Run, Script, State
from pydantic import BaseModel

from fia_api.core.utility import filter_script_for_tokens


class CountResponse(BaseModel):
    """Count response shows the count of a model"""

    count: int


class ScriptResponse(BaseModel):
    """
    ScriptResponse returns from the API a script value
    """

    value: str

    @staticmethod
    def from_script(script: Script) -> ScriptResponse:
        """
        Given a script return a ScriptResponse, filtered for tokens.
        :param script: The script to convert
        :return: The ScriptResponse object
        """
        script_to_send = filter_script_for_tokens(script.script)
        return ScriptResponse(value=script_to_send)


class PreScriptResponse(BaseModel):
    """
    PreScript response returns from the API a PreScript
    """

    value: str
    is_latest: bool
    sha: str | None = None


class RunResponse(BaseModel):
    """
    Run Response object
    """

    filename: str
    experiment_number: int
    title: str
    users: str
    run_start: datetime
    run_end: datetime
    good_frames: int
    raw_frames: int
    instrument_name: str

    @staticmethod
    def from_run(run: Run) -> RunResponse:
        """
        Given a run return a RunResponse object
        :param run: The run to convert
        :return: The RunResponse object
        """
        return RunResponse(
            filename=run.filename,
            experiment_number=run.owner.experiment_number
            if run.owner is not None and run.owner.experiment_number is not None
            else None,
            title=run.title,
            users=run.users,
            run_start=run.run_start,
            run_end=run.run_end,
            good_frames=run.good_frames,
            raw_frames=run.raw_frames,
            instrument_name=run.instrument.instrument_name,
        )


class JobResponse(BaseModel):
    """
    JobResponse object that does not contain the related runs
    """

    id: int
    start: datetime | None
    end: datetime | None
    state: State
    status_message: str | None
    inputs: Any
    outputs: str | None
    stacktrace: str | None
    script: ScriptResponse | None
    runner_image: str | None

    @staticmethod
    def from_job(job: Job) -> JobResponse:
        """
        Given a job return a JobResponse
        :param job: The Job to convert
        :return: The JobResponse object
        """
        script = ScriptResponse.from_script(job.script) if isinstance(job.script, Script) else None
        return JobResponse(
            start=job.start,
            end=job.end,
            state=job.state,
            status_message=job.status_message,
            inputs=job.inputs,
            outputs=job.outputs,
            script=script,
            stacktrace=job.stacktrace,
            id=job.id,
            runner_image=job.runner_image,
        )


class JobWithRunResponse(JobResponse):
    """
    JobWithRunsResponse is the same as a Job response, with the runs nested
    """

    run: RunResponse | None

    @staticmethod
    def from_job(job: Job) -> JobWithRunResponse:
        """
        Given a Job, return the JobWithRunsResponse
        :param job: The Job to convert
        :return: The JobWithRunsResponse Object
        """
        script = ScriptResponse.from_script(job.script) if isinstance(job.script, Script) else None
        return JobWithRunResponse(
            start=job.start,
            end=job.end,
            state=job.state,
            status_message=job.status_message,
            inputs=job.inputs,
            outputs=job.outputs,
            script=script,
            id=job.id,
            stacktrace=job.stacktrace,
            run=RunResponse.from_run(job.run) if isinstance(job.run, Run) else None,
            runner_image=job.runner_image,
        )
