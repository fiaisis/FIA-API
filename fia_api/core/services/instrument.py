""" "
Service Layer for instruments
"""

from collections.abc import Sequence
from typing import Any

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.model import Instrument
from fia_api.core.repositories import Repo
from fia_api.core.specifications.instrument import InstrumentSpecification

_REPO: Repo[Instrument] = Repo()


def get_all_instruments() -> Sequence[Instrument]:
    """Return all instruments"""
    return _REPO.find(InstrumentSpecification().all())


def get_specification_by_instrument_name(instrument_name: str) -> dict[str, Any]:
    """
    Given an instrument name, return the specification for that instrument
    :param instrument_name:
    :return:
    """
    return _REPO.find_one(InstrumentSpecification().by_name(instrument_name)).specification


def update_specification_for_instrument(instrument_name: str, specification: dict[str, Any]) -> None:
    """
    Update the specification for the given instrument name with the given specification
    :param instrument_name: The instrument name
    :param specification: The instrument specification
    :return: None
    """
    instrument = _REPO.find_one(InstrumentSpecification().by_name(instrument_name))
    if instrument is None:
        raise MissingRecordError(f"Instrument {instrument_name} does not exist")
    instrument.specification = specification
    _REPO.update_one(instrument)
