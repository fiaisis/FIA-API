"""Test cases for GEMTransform."""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.gem_transform import GEMTransform


@pytest.fixture
def script():
    """GEM Transform PreScript fixture.
    :return:"""

    return PreScript(
        value="""
        from mantid.simpleapi import SaveNexus
import numpy as np
from pathlib import Path
from isis_powder.gem import Gem


######
# autoreduction
######

config_file = "/extras/gem/Gem_config_example_25_3.yaml"

def pull_vars_from_config(config_file):
    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith("mode"):
                mode = line.split(":")[1].strip()
            elif line.startswith("vanadium_normalisation"):
                van_norm = line.split(":")[1].strip().lower()
            elif line.startswith("do_absorb_corrections"):
                do_absorb_corrections = line.split(":")[1].strip().lower()
            elif line.startswith("multiple_scattering"):
                multiple_scattering = line.split(":")[1].strip().lower()
    return mode, van_norm, do_absorb_corrections, multiple_scattering

runno = "97486"
mode, van_norm, do_absorb_corrections, multiple_scattering = pull_vars_from_config(config_file)
# Summed, Individual
input_mode = "Individual"
# Set to False to skip vanadium normalisation step
van_norm = True
# Set to True to save all intermediate workspaces, False to only save final focused workspace
save_all = True
# Set to False to skip absorption corrections
do_absorb_corrections = True
#Indicates whether to account for the effects of multiple scattering when calculating
#absorption corrections. If do_absorb_corrections is set to True this parameter must be set
multiple_scattering = True

cal_mapping_file = "calibration_mapping.yaml"
cwd = Path.cwd()
cal_mapping_file_path = Path(cwd) / cal_mapping_file

output = "/output"

gem = Gem(
    calibration_to_adjust=cal_mapping_file,
    calibration_directory=cwd, #find the calibration directory in the current working directory
    output_directory=cwd, #output files into the current working directory
    user_name="Autoreduction",
    config_file=config_file
)

gem.create_cal(run_number=runno,
               calibration_mapping_file=cal_mapping_file
)

# Vanadium only
# isis_powder checks for existing splined vanadium files.
# If they exist, create_vanadium is a no-op effectively.
# If you pre-compute vanadium and store in /extras/gem/,
# you can remove this block entirely.

gem.create_vanadium(
    calibration_mapping_file=cal_mapping_file,
    mode=mode,
    do_absorb_corrections=do_absorb_corrections,
    multiple_scattering=multiple_scattering,
    spline_coefficient=120,
    #texture_mode=True
)


# Focus
print(f"Starting focus for run {runno} with mode {mode} and input mode {input_mode}")

# Choice of cropping values for PDF or Rietveld mode
if mode == "Rietveld":
    focused_cropping_values = [
        (700, 19500),  # Bank 1
        (1000, 19500),  # Bank 2
        (1000, 19500),  # Bank 3
        (1000, 19500),  # Bank 4
        (1000, 18500),  # Bank 5
        (1000, 16750),  # Bank 6
    ]
elif mode == "PDF":
    focused_cropping_values = [
        (550, 19900),  # Bank 1
        (550, 19900),  # Bank 2
        (550, 19900),  # Bank 3
        (550, 19900),  # Bank 4
        (550, 18500),  # Bank 5
        (550, 16750),  # Bank 6
    ]
else:
    raise ValueError(f"Invalid mode: {mode}. Expected 'PDF' or 'Rietveld'.")

gem.focus(
    calibration_mapping_file=cal_mapping_file,
    do_absorb_corrections=do_absorb_corrections,
    input_mode=input_mode,
    mode=mode,
    run_number=runno,
    vanadium_normalisation=van_norm,
    unit_to_keep="dSpacing",
    keep_raw_workspace=False,
    save_all=save_all,
    focused_cropping_values=focused_cropping_values,
)

print(f"Reduction completed for run {runno}. Output files: {output}")"""
    )


@pytest.fixture
def reduction():
    """Reduction fixture"""

    mock = Mock()
    mock.inputs = {
        "mode": "transmission",
        "input_mode": "raw",
        "calibration_dir": "/path/to/cal",
        "config_file": "/path/to/config",
        "runno": 12345,
        "van_norm": True,
        "save_all": True,
        "do_asbord_corrections": True,
        "cal_mapping_file": "/path/to/cal_mapping.yaml",
    }
    return mock


def test_gem_transform_apply(script, reduction):
    """Test GEMTransform only modifies expected lines and leaves others unchanged."""
    transform = GEMTransform()
    original_lines = script.value.splitlines()

    transform.apply(script, reduction)

    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    for index, line in enumerate(updated_lines):
        if line.startswith("mode ="):
            assert line == 'mode = "transmission"'
        elif line.startswith("input_mode ="):
            assert line == 'input_mode = "raw"'
        elif line.startswith("runno ="):
            assert line == "runno = 12345"
        elif line.startswith("van_norm ="):
            assert line == 'van_norm = "True"'
        elif line.startswith("calibration_dir ="):
            assert line == "calibration_dir = /path/to/cal"
        elif line.startswith("splined_vanadium_dir ="):
            assert line == 'splined_vanadium_dir = "/path/to/splined"'
        elif line.startswith("config_file ="):
            assert line == 'config_file = "/path/to/config"'
        elif line.startswith("save_all ="):
            assert line == 'save_all = "True"'
        else:
            assert line == original_lines[index]
