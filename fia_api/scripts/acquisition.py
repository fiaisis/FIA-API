"""Acquisition module contains all the functionality for obtaining the script locally and from the remote repository"""

import logging
import os
from http import HTTPStatus
from pathlib import Path

import requests

from fia_api.core.exceptions import MissingScriptError
from fia_api.core.models import Job
from fia_api.core.utility import forbid_path_characters
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.factory import get_transform_for_instrument
from fia_api.scripts.transforms.mantid_transform import MantidTransform

logger = logging.getLogger(__name__)

LOCAL_SCRIPT_DIR = "fia_api/local_scripts"


def _get_latest_commit_sha() -> str | None:
    """
    Get the latest commit sha of the autoreduction-script repository
    :return: (str) - the commit sha
    """
    try:
        logger.info("Getting latest commit sha for autoreduction-script repo")
        response = requests.get(
            "https://api.github.com/repos/fiaisis/autoreduction-scripts/commits/HEAD",
            timeout=30,
        )

        return response.json()["sha"] if response.ok else None

    except Exception as exc:
        logger.exception(exc)
        logger.warning("Could not get latest commit sha ")
        return None


def _get_script_from_remote(instrument: str) -> PreScript:
    """
    Get the remote script for given instrument
    :param instrument: str - instrument name
    :return: Script - Returned script
    """
    try:
        logger.info("Attempting to get latest %s script...", instrument)
        request = requests.get(
            f"https://raw.githubusercontent.com/fiaisis/autoreduction-scripts/main/{instrument.upper()}/reduce.py",
            timeout=30,
        )
        if request.status_code != HTTPStatus.OK:
            logger.warning("Could not get %s script from remote", instrument)
            raise RuntimeError(f"Could not get {instrument} script from remote")
        logger.info("Obtained %s script", instrument)
        sha = _get_latest_commit_sha()
        if sha is not None:
            os.environ["sha"] = sha  # noqa: SIM112
        return PreScript(request.text, is_latest=True, sha=sha)

    except ConnectionError:
        # log exception
        logger.warning("Could not get %s script from remote", instrument)
        raise


def _get_script_locally(instrument: str) -> PreScript:
    """
    Get the local copy of the script for the given instrument
    :param instrument: str - instrument name
    :return: None
    """
    try:
        logger.info("Attempting to get %s script locally...", instrument)
        path = Path(f"{LOCAL_SCRIPT_DIR}/{instrument}.py")
        with path.open(encoding="utf-8", mode="r") as fle:
            return PreScript(value="".join(line for line in fle), sha=os.environ.get("sha", None))  # noqa: SIM112
    except FileNotFoundError as exc:
        logger.exception("Could not retrieve %s script locally", instrument)
        raise MissingScriptError(f"Unable to load any script for instrument: {instrument}") from exc


def write_script_locally(script: PreScript, instrument: str) -> None:
    """
    Write the given script locally
    :param script: Script - the script to write
    :param instrument: str - the instrument
    :return: None
    """
    if script.original_value == "":
        logger.warning("Unable to acquire any script for instrument %s", instrument)
        raise RuntimeError(f"Failed to acquire script for instrument {instrument} from remote and locally")
    if script.is_latest:
        logger.info("Updating local %s script", instrument)
        path = Path(f"{LOCAL_SCRIPT_DIR}/{instrument}.py")
        with path.open(mode="w+", encoding="utf-8") as fle:
            fle.writelines(script.original_value)


@forbid_path_characters
def get_by_instrument_name(instrument: str) -> PreScript:
    """
    Get the script object for the given instrument
    :param instrument: str - the instrument
    :return: Script - The script object
    """
    try:
        return _get_script_from_remote(instrument)
    except RuntimeError:
        return _get_script_locally(instrument)


def get_script_for_job(instrument: str, job: Job) -> PreScript:
    """
    Given an instrument and job return the transformed script for that instrument at that point in history.
    :param instrument: The instrument
    :param job: The job object. This is used to determine the correct transforms to apply to the script.
    :return: The Script
    """
    logger.info("Getting script for instrument: %s...", instrument)
    script = get_by_instrument_name(instrument)
    transform = get_transform_for_instrument(instrument)
    transform.apply(script, job)
    mantid_transform = MantidTransform()
    mantid_transform.apply(script, job)
    return script
