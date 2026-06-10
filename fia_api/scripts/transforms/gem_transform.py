import logging

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript

logger = logging.getLogger(__name__)

class GEMTransform:
    """
    GEMTransform applies modifications to GEM instrument scripts based on reduction input parameters in a Reduction
    entity.
    """
    
    def apply(self, script: PreScript, job: Job) -> None: # noqa: PLR0912,C901
        logger.info("Beginning GEM transform for job %s...", job.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the following line and see if it passes with newer mypy.
        
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
            
            if line.startswith("mode ="):
                lines[index] = f'mode = "{job.inputs["mode"]}"'  # type: ignore
                continue
            if line.startswith("input_mode ="):
                lines[index] = f'input_mode = "{job.inputs["input_mode"]}"'  # type: ignore
                continue
            if line.startswith("vanadium_runno ="):
                lines[index] = f"vanadium_runno = {runno_str}"  # type: ignore
                continue
            if line.startswith("runno ="):
                lines[index] = f"runno = {runno_str}"  # type: ignore
                continue
            if line.startswith("calibration_dir ="):
                lines[index] = f"calibration_dir = {job.inputs['calibration_dir']}"  # type: ignore
                continue
            if line.startswith("splined_vanadium_dir ="):
                lines[index] = f'splined_vanadium_dir = "{job.inputs["splined_vanadium_dir"]}"'  # type: ignore
                continue
            if line.startswith("config_file ="):
                lines[index] = f'config_file = "{job.inputs["config_file"]}"'  # type: ignore
                continue
            if line.startswith("output_dir = "):
                lines[index] = f'output_dir = "{job.inputs["output_dir"]}"'  # type: ignore
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for job %s", job.id)