"""
Module provides the EnginxTransform class, an implementation of the Transform abstract base class for ENGINX
instrument scripts.
"""

import logging

from fia_api.core.models import Job, Run
from fia_api.core.repositories import Repo
from fia_api.core.specifications.run import RunSpecification
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
                lines[index] = line.replace(line.split("=")[1], f"'{job.inputs['ceria_path']}'")
                continue

            if "vanadium_path =" in line:
                lines[index] = line.replace(line.split("=")[1], f"'{job.inputs['vanadium_path']}'")
                continue

            if "vanadium_run =" in line:
                lines[index] = self.vanadium_run_replace(line, job)
                continue

            # Transform focus_runs
            if "focus_runs =" in line:
                lines[index] = self.focus_runs_replace(line, job)
                continue

            # Transform ceria_cycle
            if "ceria_cycle =" in line:
                lines[index] = self.ceria_cycle_replace(line, job)
                continue

            # Transform ceria_run
            if "ceria_run =" in line:
                lines[index] = self.ceria_run_replace(line, job)
                continue

            # Transform group
            if "group =" in line:
                lines[index] = self.group_replace(line, job)
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for reduction %s", job.id)

    def vanadium_run_replace(self, line: str, job: Job) -> str:
        """Return a transformed vanadium_run assignment line."""
        if "ENGINX" not in str(job.inputs["vanadium_run"]):  # type: ignore
            vanadium_run = f"ENGINX{job.inputs['vanadium_run']}"  # type: ignore
        else:
            vanadium_run = job.inputs["vanadium_run"]  # type: ignore
        return line.replace(line.split("=")[1], f' "{vanadium_run}"')

    def focus_runs_replace(self, line: str, job: Job) -> str:
        """Return a transformed focus_runs assignment line using the job's run filename (without extension)."""
        run_repo: Repo[Run] = Repo()
        # The below type ignore is because of the quick fix for enginx and will be resolved in the db refactor pr
        filename = run_repo.find_one(RunSpecification().by_id(job.run_id)).filename  # type: ignore
        focus_runs = [filename.rsplit(".", 1)[0]]
        return line.replace(line.split("=")[1], f" {focus_runs!s}")

    def ceria_run_replace(self, line: str, job: Job) -> str:
        """Return a transformed ceria_run assignment line."""
        if "ENGINX" not in str(job.inputs["ceria_run"]):  # type: ignore
            ceria_run = f"ENGINX{job.inputs['ceria_run']}"  # type: ignore
        else:
            ceria_run = job.inputs["ceria_run"]  # type: ignore
        return line.replace(line.split("=")[1], f' "{ceria_run}"')

    def ceria_cycle_replace(self, line: str, job: Job) -> str:
        """Return a transformed ceria_cycle assignment line."""
        return line.replace(line.split("=")[1], f" '{job.inputs['ceria_cycle']}'")  # type: ignore

    def group_replace(self, line: str, job: Job) -> str:
        """Return a transformed group assignment line."""
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        return line.replace(line.split("=")[1], f' GROUP["{job.inputs["group"]}"]')  # type: ignore
