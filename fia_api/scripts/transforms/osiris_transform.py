"""
Module provides the OSIRISTransform class, an implementation of the Transform abstract base class for Osiris instrument
scripts.
"""

import logging
from collections.abc import Iterable

from fia_api.core.model import Reduction
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class OsirisTransform(Transform):
    """
    OsirisTransform applies modifications to MARI instrument scripts based on reduction input parameters in a Reduction
    entity.
    """

    def apply(self, script: PreScript, reduction: Reduction) -> None:
        logger.info("Beginning Osiris transform for reduction %s...", reduction.id)
        lines = script.value.splitlines()
        # MyPY does not believe ColumnElement[JSONB] is indexable, despite JSONB implementing the Indexable mixin
        # If you get here in the future, try removing the type ignore and see if it passes with newer mypy
        for index, line in enumerate(lines):
            if line.startswith("input_runs"):
                lines[index] = "input_runs = " + (
                    str(reduction.reduction_inputs["runno"])  # type:ignore
                    if isinstance(reduction.reduction_inputs["runno"], Iterable)  # type:ignore
                    else f"[{reduction.reduction_inputs['runno']}]"  # type:ignore
                )
                continue
            if line.startswith("calibration_run_number ="):
                lines[index] = (f"calibration_run_number = "
                                f"\"{reduction.reduction_inputs['calibration_run_number']}\"")  # type:ignore
                continue
            if line.startswith("cycle ="):
                lines[index] = f"cycle = \"{reduction.reduction_inputs['cycle_string']}\""  # type:ignore
                continue
            if line.startswith("analyser ="):
                lines[index] = f"analyser = \"{reduction.reduction_inputs['analyser']}\""  # type:ignore
                continue
            if line.startswith("reflection = "):
                lines[index] = f"reflection = \"{reduction.reduction_inputs['reflection']}\""  # type:ignore
                continue
            if line.startswith("spectroscopy_reduction ="):
                lines[index] = (f"spectroscopy_reduction = "
                                f"{reduction.reduction_inputs['spectroscopy_reduction'] == 'true'}")  # type:ignore
                continue
            if line.startswith("diffraction_reduction = "):
                lines[index] = (f"diffraction_reduction = "
                                f"{reduction.reduction_inputs['diffraction_reduction'] == 'true'}")  # type:ignore
                continue

        script.value = "\n".join(lines)
        logger.info("Transform complete for reduction %s", reduction.id)
