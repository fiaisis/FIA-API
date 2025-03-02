from typing import Literal

from fastapi import APIRouter, BackgroundTasks

from fia_api.core.responses import PreScriptResponse
from fia_api.scripts.acquisition import get_script_by_sha, get_script_for_job, write_script_locally
from fia_api.scripts.pre_script import PreScript

ScriptRouter = APIRouter(prefix="/instrument/{instrument}/script", tags=["scripts"])

InstrumentString = Literal[
    "ALF",
    "ARGUS",
    "CHIPIR",
    "CHRONUS",
    "CRISP",
    "EMU",
    "ENGINX",
    "GEM",
    "HIFI",
    "HRPD",
    "IMAT",
    "INES",
    "INTER",
    "IRIS",
    "LARMOR",
    "LET",
    "LOQ",
    "MAPS",
    "MARI",
    "MERLIN",
    "MUSR",
    "NIMROD",
    "OFFSPEC",
    "OSIRIS",
    "PEARL",
    "POLARIS",
    "POLREF",
    "SANDALS",
    "SANS2D",
    "SURF",
    "SXD",
    "TOSCA",
    "VESUVIO",
    "WISH",
    "ZOOM",
    "test",
    "TEST",
]


@ScriptRouter.get("/")
async def get_pre_script(
    instrument: InstrumentString,
    background_tasks: BackgroundTasks,
    job_id: int | None = None,
) -> PreScriptResponse:
    """
    Script URI - Not intended for calling
    \f
    :param instrument: the instrument
    :param background_tasks: handled by fastapi
    :param job_id: optional query parameter of runfile, used to apply transform
    :return: ScriptResponse
    """
    script = PreScript(value="")
    # This will never be returned from the api, but is necessary for the background task to run
    try:
        script = get_script_for_job(instrument, job_id)
        return script.to_response()
    finally:
        background_tasks.add_task(write_script_locally, script, instrument)
        # write the script after to not slow down request


@ScriptRouter.get("/sha/{sha}")
async def get_pre_script_by_sha(instrument: InstrumentString, sha: str, job_id: int | None = None) -> PreScriptResponse:
    """
    Given an instrument and the commit sha of a script, obtain the pre script. Optionally providing a job id to
    transform the script
    \f
    :param instrument: The instrument
    :param sha: The commit sha of the script
    :param job_id: The job id to apply transforms
    :return:
    """
    return get_script_by_sha(instrument, sha, job_id).to_response()
