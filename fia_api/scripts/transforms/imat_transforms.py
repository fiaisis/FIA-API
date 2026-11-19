"""
Module provides the IMATTransform class, an implementation of the Transform abstract base class for IMAT instrument
scripts.
"""

import logging
import re
from pathlib import Path

from fia_api.core.auth.tokens import DEV_MODE
from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)

# Matches the nGEM switch as the transform writes it (`ngem = True`) and as a hand edited script may
# spell it (`ngem = "true"`), while ignoring the `ngem = False` default the reduction ships with.
NGEM_ENABLED = re.compile(r"""^\s*ngem\s*=\s*(?:true|["']true["'])\s*$""", re.IGNORECASE)


def script_is_ngem(script: str) -> bool:
    """
    Report whether an IMAT script is configured for the nGEM detector rather than a reconstruction.

    Reruns arrive with a script that is already configured and carry no inputs of their own, so this
    is how an nGEM rerun is recognised.

    :param script: The script text to inspect.
    :return: True if the script turns the nGEM branch on.
    """
    return any(NGEM_ENABLED.match(line) for line in script.splitlines())


def _ngem_output_path(ngem_run_path: str) -> str:
    """
    Return the folder that reduced nGEM runs of the given raw run belong in.

    Reduced runs sit in a folder next to the raw cycle folder, named after it with a two digit year
    and an unpadded cycle number, and the files go directly inside it:
    /ngem/nGEM-INES/DATA/IMAT_2026_01/IMAT00038896 -> /ngem/nGEM-INES/DATA/IMAT_26_1_nxs

    Run-detection normally publishes this as an input, so this is only used when it has not.

    :param ngem_run_path: The raw nGEM run folder, e.g. .../DATA/IMAT_2026_01/IMAT00038896.
    :return: The reduced data folder for that cycle.
    """
    cycle_folder = Path(ngem_run_path).parent.name
    instrument, cycle_year, cycle_num = cycle_folder.split("_")
    reduced_folder = f"{instrument}_{cycle_year[-2:]}_{int(cycle_num)}_nxs"
    return str(Path(ngem_run_path).parent.parent / reduced_folder)


class IMATTransform(Transform):
    """
    IMATTransform applies modifications to IMAT instrument scripts based on reduction input parameters in a Reduction
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:  # noqa: C901, PLR0912
        logger.info("Beginning IMAT transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the following line and see if it passes with newer mypy.
        for index, line in enumerate(lines):
            if line.startswith("runno =") and "runno" in job.inputs:  # type: ignore
                lines[index] = f"runno = {job.inputs['runno']}"  # type: ignore
                continue
            if line.startswith("dataset_path =") and "images_dir" in job.inputs:  # type: ignore
                lines[index] = f'dataset_path = "{job.inputs["images_dir"]}"'  # type: ignore
                continue
            if line.startswith("ngem_path =") and "ngem_path" in job.inputs:  # type: ignore
                lines[index] = f'ngem_path = "{job.inputs["ngem_path"]}"'  # type: ignore
                continue
            if line.startswith("ngem ="):
                # Regardless we want to set the boolean state
                if "ngem" in job.inputs and job.inputs["ngem"] == "true":  # type: ignore
                    lines[index] = "ngem = True"
                else:
                    lines[index] = "ngem = False"
                continue
            if line.startswith("recon ="):
                # Regardless we want to set the boolean state
                if "recon" in job.inputs and job.inputs["recon"] == "true":  # type: ignore
                    lines[index] = "recon = True"
                else:
                    lines[index] = "recon = False"
                continue
            if line.startswith("output ="):
                if "ngem_path" in job.inputs and not DEV_MODE:  # type: ignore
                    # Run-detection publishes the cycle's reduced-data folder, so only derive one when
                    # the request arrived without it.
                    output_path = job.inputs.get("ngem_output_path") or _ngem_output_path(job.inputs["ngem_path"])  # type: ignore
                    lines[index] = f'output = "{output_path}"'
                else:
                    lines[index] = 'output = "/output"'
                continue
            # The nGEM reduction parameters come from the IMAT specification, via run-detection. They are
            # assigned inside the `if ngem:` block, so the four space indent and the unit comment are kept.
            if line.lstrip().startswith("start_tof =") and "start_tof" in job.inputs:  # type: ignore
                lines[index] = f"    start_tof = {job.inputs['start_tof']}  # start of the ToF range"  # type: ignore
                continue
            if line.lstrip().startswith("end_tof =") and "end_tof" in job.inputs:  # type: ignore
                lines[index] = f"    end_tof = {job.inputs['end_tof']}  # end of the ToF range"  # type: ignore
                continue
            if line.lstrip().startswith("bin_width =") and "bin_width" in job.inputs:  # type: ignore
                lines[index] = f"    bin_width = {job.inputs['bin_width']}  # TOF bin width in us"  # type: ignore
                continue
            if line.lstrip().startswith("L =") and "L" in job.inputs:  # type: ignore
                lines[index] = f"    L = {job.inputs['L']}  # moderator to detector distance"  # type: ignore
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)
