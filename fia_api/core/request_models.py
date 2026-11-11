"""Module containing the request object types for routes."""

from typing import Any

from pydantic import BaseModel, Field

from fia_api.core.models import State


class PartialJobUpdateRequest(BaseModel):
    """
    Partial Job Update Request encompasses all the safely updatable fields on a Job
    """

    state: State | None = None
    status_message: str | None = None
    outputs: str | None = None
    start: str | None = None
    stacktrace: str | None = None
    end: str | None = None


class AutoreductionRequest(BaseModel):
    """
    Autoreduction request encompasses all the fields necessary for an autoreduction job to be created
    """

    filename: str
    rb_number: str
    instrument_name: str
    title: str
    users: str
    run_start: str
    run_end: str
    good_frames: int
    raw_frames: int
    additional_values: dict[str, Any]
    runner_image: str


class LiveDataScriptUpdateRequest(BaseModel):
    """
    Script Update Request for live data
    """

    value: str


class AnalyseRequest(BaseModel):
    """
    Script analysis request forwarded to mantid-python-script-lsp.
    """

    content: str = Field(description="The script text, exactly as edited.")
    content_hash: str = Field(
        min_length=1,
        max_length=128,
        description="Client-computed digest of `content`, echoed back unchanged so the caller can "
        "discard a response for text it has already moved on from.",
    )
