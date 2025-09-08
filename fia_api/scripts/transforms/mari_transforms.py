"""
Module provides the MariTransform class, an implementation of the Transform abstract base class for MARI instrument
scripts.
"""

import logging

from sqlalchemy import ColumnElement
from sqlalchemy.dialects.postgresql import JSONB

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class MariTransform(Transform):
    """
    MariTransform applies modifications to MARI instrument scripts based on reduction input parameters in a Job
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:  # noqa: C901
        logger.info("Beginning Mari transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the type ignore and see if it passes with newer mypy
        for index, line in enumerate(lines):
            if "url_to_mask_file.xml" in line:
                lines[index] = line.replace("url_to_mask_file.xml", job.inputs["mask_file_link"])  # type: ignore
                continue
            if self._replace_input(line, lines, index, "runno", job.inputs["runno"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "sum_runs", job.inputs["sum_runs"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "ei", job.inputs["ei"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "wbvan", job.inputs["wbvan"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "monovan", job.inputs["monovan"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "sam_mass", job.inputs["sam_mass"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "sam_rmm", job.inputs["sam_rmm"]):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "git_sha", job.inputs["git_sha"]):  # type: ignore
                continue
            if self._replace_input(
                line,
                lines,
                index,
                "remove_bkg",
                job.inputs["remove_bkg"],  # type: ignore
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
