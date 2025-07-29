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
            if "vanadium_run=" in line:
                self._transform_vanadium_run(line, lines, index, job)
                continue

            # Transform focus_runs
            if "focus_runs=" in line:
                self._transform_focus_runs(line, lines, index, job)
                continue

            # Transform ceria_run
            if "ceria_run=" in line:
                self._transform_ceria_run(line, lines, index, job)
                continue

            # Placeholder for group transformation
            if "group=" in line:
                self._transform_group(line, lines, index, job)
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for reduction %s", job.id)

    def _transform_vanadium_run(self, line: str, lines: list[str], index: int, job: Job) -> None:
        """
        Transform the vanadium_run parameter in the script.

        :param line: The current line
        :param lines: All lines in the script
        :param index: The index of the current line
        :param job: The job containing the parameters
        :return: None
        """
        if "ENGINX" not in job.inputs["vanadium_run"]:  # type: ignore
            vanadium_run = f"ENGINX{job.inputs['vanadium_run']}"  # type: ignore
        else:
            vanadium_run = job.inputs["vanadium_run"]  # type: ignore
        lines[index] = line.replace(line.split("=")[1], f'"{vanadium_run}"')

    def _transform_focus_runs(self, line: str, lines: list[str], index: int, job: Job) -> None:
        """
        Transform the focus_runs parameter in the script.

        :param line: The current line
        :param lines: All lines in the script
        :param index: The index of the current line
        :param job: The job containing the parameters
        :return: None
        """
        focus_runs = [job.run.filename.rsplit(".", 1)[0]]
        lines[index] = line.replace(line.split("=")[1], str(focus_runs))

    def _transform_ceria_run(self, line: str, lines: list[str], index: int, job: Job) -> None:
        """
        Transform the ceria_run parameter in the script.

        :param line: The current line
        :param lines: All lines in the script
        :param index: The index of the current line
        :param job: The job containing the parameters
        :return: None
        """
        if "ENGINX" not in job.inputs["ceria_run"]:  # type: ignore
            ceria_run = f"ENGINX{job.inputs['ceria_run']}"  # type: ignore
        else:
            ceria_run = job.inputs["ceria_run"]  # type: ignore
        lines[index] = line.replace(line.split("=")[1], f'"{ceria_run}"')

    def _transform_group(self, line: str, lines: list[str], index: int, job: Job) -> None:
        """
        Transform the group parameter in the script.
        This is a placeholder for future implementation.

        :param line: The current line
        :param lines: All lines in the script
        :param index: The index of the current line
        :param job: The job containing the parameters
        :return: None
        """
        lines[index] = line.replace(line.split("=")[1], f'GROUP["{job.inputs["group"]}"]')
