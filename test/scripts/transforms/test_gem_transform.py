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
        value="""from pathlib import Path
from isis_powder.gem import Gem
from isis_powder.routines import yaml_parser
from isis_powder import SampleDetails
import os
import shutil
import yaml


######
# autoreduction
######

runno = "96789"
# Set the mode for reduction
mode = "Rietveld"
# Set to False to skip vanadium normalisation step
van_norm = True
# Set to False to skip absorption corrections
do_absorb_corrections = False
# Indicates whether to account for the effects of multiple scattering when calculating
# absorption corrections. If do_absorb_corrections is set to True this parameter must be set.
multiple_scattering = False
# Summed, Individual
input_mode = "Individual"
# Set to True to save all intermediate workspaces, False to only save final focused workspace
save_all = True

cycle = "cycle_25_1"


offset_file = "offsets_2023_cycle231.cal"
offset_file_base_path = Path(f"C:\\Path\\to\\{offset_file}")
rietveldvanrunnumbers = "96663"
rietveldemptyrunnumbers = "96664"
pdfvanrunnumbers = "97483"
pdfemptyrunnumbers = "97484"
first_cycle_run_no=int(runno) - 1

mapping_file_data = {
    f"{int(rietveldvanrunnumbers) - 1}-{runno}": {"label": f"{cycle}", "offset_file_name": f"{offset_file}",
                             "Rietveld": {"vanadium_run_numbers": f"{rietveldvanrunnumbers}",
                                    "empty_run_numbers": f"{rietveldemptyrunnumbers}"},
                              "PDF": {"vanadium_run_numbers": f"{pdfvanrunnumbers}",
                                    "empty_run_numbers": f"{pdfemptyrunnumbers}"}}
}


cal_mapping_file = f"GEM_{cycle}_calibration_mapping.yaml"
calibration_directory = Path("/Calibrations")
cal_cycle_path = Path(calibration_directory, cycle)
print(f"creating dir {cal_cycle_path}")
Path.mkdir(cal_cycle_path, exist_ok=True)
print(f"Moving {offset_file} into {cal_cycle_path}")
shutil.copy(offset_file_base_path, cal_cycle_path)

cal_mapping_file_path = Path(calibration_directory, cal_mapping_file)
offset_file_path = Path(calibration_directory, offset_file)

def generate_mapping_file(cal_mapping_file_path, mapping_file_data):
    try:
        print(f"creating mapping file with {mapping_file_data}:")
        with open(cal_mapping_file_path, 'w') as f:
            yaml.dump(mapping_file_data, f)
    except Exception as e:
        print(f"Error occurred while generating mapping file: {e}")

print(f"Generating mapping file {cal_mapping_file}")
generate_mapping_file(cal_mapping_file_path, mapping_file_data)

output = "/output"
output_directory="/output"

gem = Gem(
    calibration_directory="/Calibrations",
    output_directory="/output",
    user_name="Autoreduction",
    mode = mode,
    vanadium_normalisation=van_norm,
    do_absorb_corrections=do_absorb_corrections,
    input_mode=input_mode,
    save_all=save_all,
    mayers_mult_scat_events=100 #reduce points for monte carlo sim for testing, remove for prod
)


gem.create_vanadium(
    first_cycle_run_no=first_cycle_run_no,
    calibration_mapping_file=cal_mapping_file_path,
    mode=mode,
    do_absorb_corrections=True, #these need to be true for vanadium
    multiple_scattering=True, #Might need to be true always
    spline_coefficient=30,
    texture_mode=False
)


# Focus

gem.focus(
    calibration_mapping_file=cal_mapping_file_path,
    do_absorb_corrections=do_absorb_corrections,
    multiple_scattering=False,
    input_mode=input_mode,
    mode=mode,
    run_number=runno,
    unit_to_keep="dSpacing",
    keep_raw_workspace=False,
    save_all=save_all,
    #focused_cropping_values=focused_cropping_values,
)

print(f"Reduction completed for run {runno}. Output files: {output_directory}")
"""
    )


@pytest.fixture
def reduction():
    """Reduction fixture"""

    mock = Mock()
    mock.inputs = {
        "cycle": "cycle_25_3",
        "mode": "transmission",
        "input_mode": "raw",
        "calibration_dir": "/path/to/cal",
        "runno": 12345,
        "van_norm": True,
        "save_all": True,
        "do_absorb_corrections": True,
        "multiple_scattering": True,
        "rietveldvanrunnumbers": "96663",
        "rietveldemptyrunnumbers": "96664",
        "pdfvanrunnumbers": "97483",
        "pdfemptyrunnumbers": "97484",
        "offset_file": "offsets_2023_cycle231.cal",
    }
    return mock


def test_gem_transform_runno_list(script, reduction):
    """Test GEMTransform handles runno as a list correctly."""
    reduction.inputs["runno"] = [12345, 12346, 12347]
    transform = GEMTransform()
    transform.apply(script, reduction)
    updated_lines = script.value.splitlines()
    for line in updated_lines:
        if line.startswith("runno ="):
            assert line == "runno = 12345-12347"


def test_gem_transform_apply(script, reduction):  # noqa: C901, PLR0912
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
        elif line.startswith("calibration_dir ="):
            assert line == "calibration_dir = /path/to/cal"
        elif line.startswith("runno ="):
            assert line == "runno = 12345"
        elif line.startswith("van_norm ="):
            assert line == 'van_norm = "True"'
        elif line.startswith("save_all ="):
            assert line == 'save_all = "True"'
        elif line.startswith("do_absorb_corrections ="):
            assert line == 'do_absorb_corrections = "True"'
        elif line.startswith("multiple_scattering ="):
            assert line == 'multiple_scattering = "True"'
        elif line.startswith("rietveldvanrunnumbers ="):
            assert line == "rietveldvanrunnumbers = 96663"
        elif line.startswith("rietveldemptyrunnumbers ="):
            assert line == "rietveldemptyrunnumbers = 96664"
        elif line.startswith("pdfvanrunnumbers ="):
            assert line == "pdfvanrunnumbers = 97483"
        elif line.startswith("pdfemptyrunnumbers ="):
            assert line == "pdfemptyrunnumbers = 97484"
        elif line.startswith("cycle ="):
            assert line == 'cycle = "cycle_25_3"'
        elif line.startswith("offset_file = "):
            assert line == 'offset_file = "offsets_2023_cycle231.cal"'
        else:
            assert line == original_lines[index]
