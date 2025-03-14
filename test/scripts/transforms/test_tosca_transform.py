"""Test for tosca transform"""

from unittest.mock import Mock

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.tosca_transform import ToscaTransform

SCRIPT = """from mantid.simpleapi import *


def generate_input_path_for_run(run_number):
    return f"/archive/ndxtosca/Instrument/data/{cycle}/TSC{run_number}.nxs"


# To change by automatic script
input_runs = ["25240", "25241"]
cycle = "cycle_19_4"

# Defaults
instrument = "TOSCA"
analyser = "graphite"
reflection = "002"
spectra_range = "1,140"
rebin_string = "-2.5,0.015,3,-0.005,1000"
unit_x = "DeltaE_inWavenumber"

# Generated
sum_runs = len(input_runs) > 1

input_file_paths = ""
for input_run in input_runs:
    input_file_paths += ", " + generate_input_path_for_run(input_run)
input_file_paths = input_file_paths[2:]

print(input_file_paths)
original_ws = Load(generate_input_path_for_run(input_runs[0]))
run_title = original_ws.getTitle()
output_workspace_name = f"{instrument.lower()}{input_run}-{run_title}"

# Run the script
output_ws = ISISIndirectEnergyTransferWrapper(InputFiles=input_file_paths,
                                              SumFiles=sum_runs,
                                              Instrument=instrument,
                                              Analyser=analyser,
                                              Reflection=reflection,
                                              SpectraRange=spectra_range,
                                              RebinString=rebin_string,
                                              UnitX=unit_x,
                                              OutputWorkspace=output_workspace_name)

# Save out the workspace
if output_ws.isGroup():
    # Assume only 1 output workspace is present, this is the assumption as SumFiles should be true if inputs is great than 1.
    output_ws = output_ws.getItem(0)

save_file_name = f"{output_ws.name()}.nxs"
save_path = f"/output/"

SaveNexusProcessed(output_ws, f"{save_path}{save_file_name}")

# Setup the output variable
output = save_file_name"""
EXPECTED_SCRIPT = """from mantid.simpleapi import *


def generate_input_path_for_run(run_number):
    return f"/archive/ndxtosca/Instrument/data/{cycle}/TSC{run_number}.nxs"


# To change by automatic script
input_runs = ["1", "2", "3"]
cycle = "cycle_23_3"

# Defaults
instrument = "TOSCA"
analyser = "graphite"
reflection = "002"
spectra_range = "1,140"
rebin_string = "-2.5,0.015,3,-0.005,1000"
unit_x = "DeltaE_inWavenumber"

# Generated
sum_runs = len(input_runs) > 1

input_file_paths = ""
for input_run in input_runs:
    input_file_paths += ", " + generate_input_path_for_run(input_run)
input_file_paths = input_file_paths[2:]

print(input_file_paths)
original_ws = Load(generate_input_path_for_run(input_runs[0]))
run_title = original_ws.getTitle()
output_workspace_name = f"{instrument.lower()}{input_run}-{run_title}"

# Run the script
output_ws = ISISIndirectEnergyTransferWrapper(InputFiles=input_file_paths,
                                              SumFiles=sum_runs,
                                              Instrument=instrument,
                                              Analyser=analyser,
                                              Reflection=reflection,
                                              SpectraRange=spectra_range,
                                              RebinString=rebin_string,
                                              UnitX=unit_x,
                                              OutputWorkspace=output_workspace_name)

# Save out the workspace
if output_ws.isGroup():
    # Assume only 1 output workspace is present, this is the assumption as SumFiles should be true if inputs is great than 1.
    output_ws = output_ws.getItem(0)

save_file_name = f"{output_ws.name()}.nxs"
save_path = f"/output/"

SaveNexusProcessed(output_ws, f"{save_path}{save_file_name}")

# Setup the output variable
output = save_file_name"""


def test_tosca_transform() -> None:
    """Test updates on script are expected"""
    job = Mock()
    job.inputs = {
        "input_runs": [1, 2, 3],
        "cycle_string": "cycle_23_3",
    }
    transform = ToscaTransform()
    script = PreScript(value=SCRIPT)
    transform.apply(script, job)
    assert script.value == EXPECTED_SCRIPT
