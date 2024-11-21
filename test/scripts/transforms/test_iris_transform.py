"""Test Case for osiris transforms"""

# pylint: disable = line-too-long
from unittest.mock import Mock

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.iris_transform import IrisTransform

SCRIPT = """from mantid.simpleapi import *


def generate_input_path_for_run(run_number, cycle):
    return f"/archive/ndxiris/Instrument/data/{cycle}/IRIS{run_number}.nxs"


# To change by automatic script
input_runs = [105277]
calibration_run_numbers = [105313, 105315, 105317]
cycle = "cycle_24_3"
analyser = "graphite"
reflection = "002"

if not diffraction_reduction and not spectroscopy_reduction:
    raise RuntimeError("diffraction_reduction and spectroscopy_reduction are both false, so this will do nothing.")

# Defaults and other generated inputs
instrument = "IRIS"
instrument_definition_directory = ConfigService.Instance().getString("instrumentDefinition.directory")
instrument_filename = instrument_definition_directory + instrument + "_Definition.xml"
instrument_workspace = LoadEmptyInstrument(Filename=instrument_filename, OutputWorkspace="instrument_workspace")
parameter_filename = instrument_definition_directory + instrument + "_" + analyser + "_" + reflection \
    + "_Parameters.xml"
parameter_file = LoadParameterFile(Filename=parameter_filename, Workspace="instrument_workspace")
efixed = instrument_workspace.getInstrument().getComponentByName(analyser).getNumberParameter("Efixed")[0]
spec_spectra_range = "3,53"
diff_spectra_range = '105,112'
unit_x = "DeltaE"
fold_multiple_frames = False"""


def create_expected_script(
    input_runs,
    calibration_run_numbers,
    cycle,
    analyser,
    reflection,
) -> str:
    """Generate an expected script for assertion"""
    return f"""from mantid.simpleapi import *


def generate_input_path_for_run(run_number, cycle):
    return f"/archive/ndxiris/Instrument/data/{{cycle}}/IRIS{{run_number}}.nxs"


# To change by automatic script
input_runs = {input_runs}
calibration_run_numbers = [{calibration_run_numbers}]
cycle = "{cycle}"
analyser = "{analyser}"
reflection = "{reflection}"

if not diffraction_reduction and not spectroscopy_reduction:
    raise RuntimeError("diffraction_reduction and spectroscopy_reduction are both false, so this will do nothing.")

# Defaults and other generated inputs
instrument = "IRIS"
instrument_definition_directory = ConfigService.Instance().getString("instrumentDefinition.directory")
instrument_filename = instrument_definition_directory + instrument + "_Definition.xml"
instrument_workspace = LoadEmptyInstrument(Filename=instrument_filename, OutputWorkspace="instrument_workspace")
parameter_filename = instrument_definition_directory + instrument + "_" + analyser + "_" + reflection \
    + "_Parameters.xml"
parameter_file = LoadParameterFile(Filename=parameter_filename, Workspace="instrument_workspace")
efixed = instrument_workspace.getInstrument().getComponentByName(analyser).getNumberParameter("Efixed")[0]
spec_spectra_range = "3,53"
diff_spectra_range = '105,112'
unit_x = "DeltaE"
fold_multiple_frames = False"""


def test_iris_transform_spectroscopy():
    """Test spectroscopy transform"""
    job = Mock()
    job.inputs = {
        "input_runs": [1, 2, 3],
        "calibration_run_numbers": "105313, 105315, 105317",
        "cycle_string": "cycle_1_2",
        "analyser": "graphite",
        "reflection": "002",
    }
    script = PreScript(value=SCRIPT)
    IrisTransform().apply(script, job)

    assert script.value == create_expected_script(
        input_runs="[1, 2, 3]",
        calibration_run_numbers="105313, 105315, 105317",
        cycle="cycle_1_2",
        analyser="graphite",
        reflection="002",
    )
