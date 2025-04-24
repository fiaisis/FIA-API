"""Specifications for Runs"""

from __future__ import annotations

from sqlalchemy import select

from fia_api.core.models import Run
from fia_api.core.specifications.base import Specification


class RunSpecification(Specification[Run]):
    @property
    def model(self) -> type[Run]:
        return Run

    def by_filename(self, filename: str) -> RunSpecification:
        self.value = select(Run).where(Run.filename == filename)
        return self
