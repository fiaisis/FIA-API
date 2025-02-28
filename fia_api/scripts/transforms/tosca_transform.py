"""Module for Tosca script transform"""

import logging

from db.data_models import Job

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class ToscaTransform(Transform):
    """Tosca Transform applies modifications to tosca script based on the job inputs"""

    # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
    # If you get here in the future, try removing the type ignore and see if it passes with newer mypy.
    def apply(self, script: PreScript, job: Job) -> None:
        logger.info("Beginning Tosca transform for job: %s...", job.id)
        lines = script.value.splitlines()
        for index, line in enumerate(lines):
            if line == 'input_runs = ["25240", "25241"]':
                lines[index] = self._generate_input_runs_line(job)
                continue
            if line == 'cycle = "cycle_19_4"':
                lines[index] = f'cycle = "{job.inputs["cycle_string"]}"'  # type: ignore
                break
        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)

    @staticmethod
    def _generate_input_runs_line(job: Job) -> str:
        run_numbers = [f'"{run_number}"' for run_number in job.inputs["input_runs"]]  # type: ignore
        return f"input_runs = [{', '.join(run_numbers)}]"
