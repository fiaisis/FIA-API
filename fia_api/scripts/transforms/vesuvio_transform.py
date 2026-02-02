"""
Module provides the VesuvioTransform class, an implementation of the Transform abstract base class for VESUVIO
instrument scripts.
"""

import logging

from sqlalchemy import ColumnElement
from sqlalchemy.dialects.postgresql import JSONB

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class VesuvioTransform(Transform):
    """
    VesuvioTransform applies modifications to VESUVIO instrument scripts based on reduction input parameters in a Job
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:
        logger.info("Beginning Vesuvio transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the type ignore and see if it passes with newer mypy

        runno = job.inputs["runno"]  # type: ignore
        if isinstance(runno, list):
            if len(runno) > 1:
                # Convert list to range string if contiguous, otherwise comma-separated
                if all(runno[i] == runno[i - 1] + 1 for i in range(1, len(runno))):
                    runno_str = f"{runno[0]}-{runno[-1]}"
                else:
                    runno_str = ",".join(map(str, runno))
            else:
                runno_str = str(runno[0])
        else:
            runno_str = str(runno)

        for index, line in enumerate(lines):
            if self._replace_input(line, lines, index, "ip", f'"{job.inputs["ip_file"]}"'):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "runno", f'"{runno_str}"'):  # type: ignore
                continue
            if self._replace_input(line, lines, index, "empty_runs", f'"{job.inputs["empty_runs"]}"'):  # type: ignore
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
