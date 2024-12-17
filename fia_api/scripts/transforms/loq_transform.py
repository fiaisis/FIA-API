"""
Module provides the LoqTransform class, an implementation of the Transform abstract base class for LOQ instrument
scripts.
"""

import logging

from db.data_models import Job
from sqlalchemy import ColumnElement
from sqlalchemy.dialects.postgresql import JSONB

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


# mypy: disable-error-code="operator, index"
class LoqTransform(Transform):
    """
    LoqTransform applies modifications to LOQ instrument scripts based on reduction input parameters in a Job
    entity.
    """
    def apply(self, script: PreScript, job: Job) -> None:  # noqa: C901
        logger.info("Beginning LOQ transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the type ignore and see if it passes with newer mypy
        for index, line in enumerate(lines):
            if "/extras/loq/MaskFile.toml" in line and "user_file" in job.inputs:
                lines[index] = line.replace("/extras/loq/MaskFile.toml", job.inputs["user_file"])
                continue
            if "run_number" in job.inputs and self._replace_input(
                line, lines, index, "sample_scatter", job.inputs["run_number"]
            ):
                continue
            if "scatter_transmission" in job.inputs and self._replace_input(
                line, lines, index, "sample_transmission", job.inputs["scatter_transmission"]
            ):
                continue
            if "scatter_direct" in job.inputs and self._replace_input(
                line, lines, index, "sample_direct", job.inputs["scatter_direct"]
            ):
                continue
            if "can_scatter" in job.inputs and self._replace_input(
                line, lines, index, "can_scatter", job.inputs["can_scatter"]
            ):
                continue
            if "can_transmission" in job.inputs and self._replace_input(
                line, lines, index, "can_transmission", job.inputs["can_transmission"]
            ):
                continue
            if "can_direct" in job.inputs and self._replace_input(
                line, lines, index, "can_direct", job.inputs["can_direct"]
            ):
                continue
            if "sample_thickness" in job.inputs and self._replace_input(
                line, lines, index, "sample_thickness", job.inputs["sample_thickness"]
            ):
                continue
            if "sample_geometry" in job.inputs and self._replace_input(
                line, lines, index, "sample_geometry", '"' + job.inputs["sample_geometry"] + '"'
            ):
                continue
            if "sample_height" in job.inputs and self._replace_input(
                line, lines, index, "sample_height", job.inputs["sample_height"]
            ):
                continue
            if "sample_width" in job.inputs and self._replace_input(
                line, lines, index, "sample_width", job.inputs["sample_width"]
            ):
                continue
        script.value = "\n".join(lines)
        logger.info("Transform complete for reduction %s", job.id)

    @staticmethod
    def _replace_input(
        line: str,
        lines: list[str],
        index: int,
        line_start: str,
        replacement: ColumnElement["JSONB"],
    ) -> bool:
        if line.startswith(line_start):
            lines[index] = f"{line_start} = {replacement}"
            return True
        return False
