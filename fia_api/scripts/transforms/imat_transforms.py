"""
Module provides the IMATTransform class, an implementation of the Transform abstract base class for IMAT instrument
scripts.
"""

import logging

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class IMATTransform(Transform):
    """
    IMATTransform applies modifications to IMAT instrument scripts based on reduction input parameters in a Reduction
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:
        logger.info("Beginning IMAT transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the following line and see if it passes with newer mypy.
        for index, line in enumerate(lines):
            if line.startswith("runno ="):
                lines[index] = f'runno = {job.inputs["runno"]}'  # type: ignore
                continue
            if line.startswith("dataset_path = "):
                lines[index] = f'dataset_path = Path("{job.inputs["images_dir"]}")'  # type: ignore
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)
