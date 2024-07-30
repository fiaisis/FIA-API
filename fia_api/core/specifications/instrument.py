"""Specification for instrument"""

from __future__ import annotations

from db.data_models import Instrument
from sqlalchemy import select

from fia_api.core.specifications.base import Specification


class InstrumentSpecification(Specification[Instrument]):
    @property
    def model(self) -> type[Instrument]:
        return Instrument

    def by_name(self, name: str) -> InstrumentSpecification:
        self.value = select(Instrument).where(Instrument.instrument_name == name)
        return self
