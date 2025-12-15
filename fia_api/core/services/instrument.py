"""Service Layer for instruments"""

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.models import Instrument
from fia_api.core.repositories import Repo
from fia_api.core.specifications.instrument import InstrumentSpecification



def get_instrument_by_name(instrument_name: str, session: Session) -> Instrument:
    repo: Repo[Instrument] = Repo(session)
    instrument = repo.find_one(InstrumentSpecification().by_name(instrument_name))
    if instrument is None:
        raise MissingRecordError("Instrument not found")
    return instrument


def get_specification_by_instrument_name(instrument_name: str, session: Session) -> JSONB | None:
    """
    Given an instrument name, return the specification for that instrument
    :param instrument_name:
    :return:
    """
    return get_instrument_by_name(instrument_name, session).specification


def update_specification_for_instrument(instrument_name: str, specification: dict[str, Any], session: Session) -> None:
    """
    Update the specification for the given instrument name with the given specification
    :param instrument_name: The instrument name
    :param specification: The instrument specification
    :return: None
    """
    repo: Repo[Instrument] = Repo(session)
    instrument = get_instrument_by_name(instrument_name, session)
    instrument.specification = specification  # type: ignore  # Problem with sqlalchemy typing
    repo.update_one(instrument)


def get_latest_run_by_instrument_name(instrument_name: str, session: Session) -> str | None:
    """
    Given an instrument name, return the latest run for that instrument
    :param instrument_name: The instrument name
    :return: The latest run or None if not found
    """
    return get_instrument_by_name(instrument_name, session).latest_run


def update_latest_run_for_instrument(instrument_name: str, latest_run: str, session: Session) -> None:
    """
    Update the latest run for the given instrument name
    :param instrument_name: The instrument name
    :param latest_run: The latest run
    :return: None
    """
    repo: Repo[Instrument] = Repo(session)
    instrument = get_instrument_by_name(instrument_name, session)
    instrument.latest_run = latest_run
    repo.update_one(instrument)


def get_live_data_script_by_instrument_name(instrument_name: str, session: Session) -> str | None:
    """
    Return the stored live data script for this instrument (or None)
    :param instrument_name: The instrument name
    :return: The script string or None
    """
    return get_instrument_by_name(instrument_name, session).live_data_script


def update_live_data_script_for_instrument(instrument_name: str, script: str, session: Session) -> None:
    """
    Update the stored live data script for this instrument
    :param instrument_name: The instrument name
    :param script: The python script content
    :return: None
    """
    repo: Repo[Instrument] = Repo(session)
    instrument = get_instrument_by_name(instrument_name, session)
    instrument.live_data_script = script
    repo.update_one(instrument)
