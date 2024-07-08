""" "
Service Layer for instruments
"""

from typing import Any

from sqlalchemy.dialects.postgresql import JSONB

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.model import Instrument
from fia_api.core.repositories import Repo
from fia_api.core.specifications.instrument import InstrumentSpecification

_REPO: Repo[Instrument] = Repo()


def get_specification_by_instrument_name(instrument_name: str) -> JSONB:
    """
    Given an instrument name, return the specification for that instrument
    :param instrument_name:
    :return:
    """
    instrument = _REPO.find_one(InstrumentSpecification().by_name(instrument_name))
    if instrument is None:
        raise MissingRecordError("Instrument not found")
    return instrument.specification


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
    instrument.specification = specification  # type: ignore  # Problem with sqlalchemy typing
    _REPO.update_one(instrument)
