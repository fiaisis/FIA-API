"""Specification for instrument"""

from __future__ import annotations

from sqlalchemy import select

from fia_api.core.models import Instrument
from fia_api.core.specifications.base import Specification


class InstrumentSpecification(Specification[Instrument]):
    @property
    def model(self) -> type[Instrument]:
        return Instrument

    def by_name(self, name: str) -> InstrumentSpecification:
        self.value = select(Instrument).where(Instrument.instrument_name == name)
        return self

    def with_live_data_support(self) -> InstrumentSpecification:
        """Filter to only instruments that support live data."""
        self.value = select(Instrument).where(Instrument.live_data_support.is_(True))
        return self
