"""
Module provides the EnginxTransform class, an implementation of the Transform abstract base class for ENGINX
instrument scripts.
"""

import logging

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class EnginxTransform(Transform):
    """
    EnginxTransform applies modifications to ENGINX instrument scripts based on reduction input parameters in a Job
    entity.
    """

    def apply(self, script: PreScript, job: Job) -> None:
        """
        Apply the EnginxTransform to the script based on job parameters.

        :param script: The script to transform
        :param job: The job containing the parameters
        :return: None
        """
        logger.info("Beginning Enginx transform for job %s...", job.id)
        lines = script.value.splitlines()

        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the type ignore and see if it passes with newer mypy
        for index, line in enumerate(lines):
            # Transform vanadium_run (always prefixed with ENGINX)
            if "ceria_path =" in line:
                lines[index] = line.replace(line.split("=")[1], f"'{job.inputs['ceria_path']}'")  # type: ignore
                continue

            if "vanadium_path =" in line:
                lines[index] = line.replace(line.split("=")[1], f"'{job.inputs['vanadium_path']}'")  # type: ignore
                continue

            if "focus_path =" in line:
                lines[index] = line.replace(line.split("=")[1], f"'{job.inputs['focus_path']}'")  # type: ignore
                continue

            # Transform group
            if "group =" in line:
                lines[index] = self.group_replace(line, job)
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for reduction %s", job.id)

    def group_replace(self, line: str, job: Job) -> str:
        """
        Given the line, replace the group with the group specified in the job.
        :param line: The line to transform
        :param job: The job containing the group
        :return: The transformed line
        """
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        return line.replace(line.split("=")[1], f' GROUP["{job.inputs["group"]}"]')  # type: ignore
