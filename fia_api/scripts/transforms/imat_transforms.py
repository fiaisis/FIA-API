"""
Module provides the IMATTransform class, an implementation of the Transform abstract base class for IMAT instrument
scripts.
"""

import logging
from pathlib import Path

from fia_api.core.auth.tokens import DEV_MODE
from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


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
            if line.startswith("runno =") and "runno" in job.inputs:
                lines[index] = f"runno = {job.inputs['runno']}"  # type: ignore
                continue
            if line.startswith("dataset_path = ") and "images_dir" in job.inputs:
                lines[index] = f'dataset_path = "{job.inputs["images_dir"]}"'  # type: ignore
                continue
            if line.startswith("ngem_path =") and "ngem_path" in job.inputs:
                lines[index] = f'ngem_path = "{job.inputs["ngem_path"]}"'
                continue
            if line.startswith("ngem ="):
                # Regardless we want to set the boolean state
                if "ngem" in job.inputs and job.inputs["ngem"] == "true":
                    lines[index] = "ngem = True"
                else:
                    lines[index] = "ngem = False"
                continue
            if line.startswith("recon ="):
                # Regardless we want to set the boolean state
                if "recon" in job.inputs and job.inputs["recon"] == "true":
                    lines[index] = "recon = True"
                else:
                    lines[index] = "recon = False"
                continue
            if line.startswith("output_path ="):
                if "ngem_path" in job.inputs and not DEV_MODE:
                    output_path = f"\"{Path(job.inputs['ngem_path']).parent}\""
                else:
                    output_path = '"/output"'
                lines[index] = f"output_path = {output_path}"
                continue


        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)
