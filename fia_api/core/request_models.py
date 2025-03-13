"""Module containing the request object types for routes."""

from db.data_models import State
from pydantic import BaseModel


class PartialJobUpdateRequest(BaseModel):
    """
    Partial Job Update Request encompasses all the safely updatable fields on a Job
    """

    state: State | None = None
    status_message: str | None = None
    outputs: list[str] | None = None
    start: str | None = None
    stacktrace: str | None = None
    end: str | None = None
