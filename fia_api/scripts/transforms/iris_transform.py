"""
Module provides the IRISTransform class, an implementation of the Transform abstract base class for Iris instrument
scripts.
"""

import logging
from collections.abc import Iterable

from db.data_models import Job

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class IrisTransform(Transform):
    """
    IrisTransform applies modifications to IRIS instrument scripts based on reduction input parameters in a Reduction
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:
        logger.info("Beginning Iris transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the following line and see if it passes with newer mypy.
        for index, line in enumerate(lines):
            if line.startswith("input_runs"):
                lines[index] = "input_runs = " + (
                    str(job.inputs["input_runs"])  # type: ignore
                    if isinstance(job.inputs["input_runs"], Iterable)  # type: ignore
                    else f"[{job.inputs['input_runs']}]"  # type: ignore
                )
                continue
            if line.startswith("calibration_run_number ="):
                lines[index] = f"calibration_run_number = \"{job.inputs['calibration_run_number']}\""  # type: ignore
                continue
            if line.startswith("cycle ="):
                lines[index] = f"cycle = \"{job.inputs['cycle_string']}\""  # type: ignore
                continue
            if line.startswith("analyser ="):
                lines[index] = f"analyser = \"{job.inputs['analyser']}\""  # type: ignore
                continue
            if line.startswith("reflection = "):
                lines[index] = f"reflection = \"{job.inputs['reflection']}\""  # type: ignore
                continue
            if line.startswith("spectroscopy_reduction ="):
                lines[index] = f"spectroscopy_reduction = {job.inputs['spectroscopy_reduction'] == 'true'}"  # type: ignore
                continue
            if line.startswith("diffraction_reduction = "):
                lines[index] = f"diffraction_reduction = {job.inputs['diffraction_reduction'] == 'true'}"  # type: ignore
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)
