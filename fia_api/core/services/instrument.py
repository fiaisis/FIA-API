"""Service Layer for instruments"""

from typing import Any

from sqlalchemy.dialects.postgresql import JSONB

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.models import Instrument
from fia_api.core.repositories import Repo
from fia_api.core.specifications.instrument import InstrumentSpecification

_REPO: Repo[Instrument] = Repo()

def get_instrument_by_name(instrument: str) -> Instrument:
    instrument = _REPO.find_one(InstrumentSpecification().by_name(instrument))
    if instrument is None:
        raise MissingRecordError("Instrument not found")
    return instrument

def get_specification_by_instrument_name(instrument_name: str) -> JSONB | None:
    """
    Given an instrument name, return the specification for that instrument
    :param instrument_name:
    :return:
    """
    return get_instrument_by_name(instrument_name).specification


def update_specification_for_instrument(instrument_name: str, specification: dict[str, Any]) -> None:
    """
    Update the specification for the given instrument name with the given specification
    :param instrument_name: The instrument name
    :param specification: The instrument specification
    :return: None
    """
    instrument = get_instrument_by_name(instrument_name)
    instrument.specification = specification  # type: ignore  # Problem with sqlalchemy typing
    _REPO.update_one(instrument)


def get_latest_run_by_instrument_name(instrument_name: str) -> str | None:
    """
    Given an instrument name, return the latest run for that instrument
    :param instrument_name: The instrument name
    :return: The latest run or None if not found
    """
    return get_instrument_by_name(instrument_name).latest_run


def update_latest_run_for_instrument(instrument_name: str, latest_run: str) -> None:
    """
    Update the latest run for the given instrument name
    :param instrument_name: The instrument name
    :param latest_run: The latest run
    :return: None
    """
    instrument = get_instrument_by_name(instrument_name)
    instrument.latest_run = latest_run
    _REPO.update_one(instrument)


def get_live_data_script_by_instrument_name(instrument_name: str) -> str | None:
    """
    Return the stored live data script for this instrument (or None)
    :param instrument_name: The instrument name
    :return: The script string or None
    """
    return get_instrument_by_name(instrument_name).live_data_script


def update_live_data_script_for_instrument(instrument_name: str, script: str) -> None:
    """
    Update the stored live data script for this instrument
    :param instrument_name: The instrument name
    :param script: The python script content
    :return: None
    """
    instrument = get_instrument_by_name(instrument_name)
    instrument.live_data_script = script
    _REPO.update_one(instrument)
