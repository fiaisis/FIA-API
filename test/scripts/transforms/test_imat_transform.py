"""Test Case for IMAT transforms"""

import ast
from unittest.mock import Mock, patch

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.imat_transforms import (
    IMATTransform,
    _ngem_output_path,
    _ngem_tof_assignment,
    script_is_ngem,
)

SCRIPT = """
FILTERS = {f.__name__: f for f in load_filter_packages()}
RECON_DEFAULT_SETTINGS = {'algorithm': 'FBP_CUDA', 'filter_name': 'ram-lak', 'cor': 1, 'tilt': 0}
DEBUG = False
DEBUG_DIR = Path("/output/debug")


# To be edited by us for the script
runno = 112345
dataset_path = Path("/home/ubuntu/large")
ngem_path = "/path/to/ngem"
ngem = False
recon = False
output = "/output"
"""

# The nGEM parameters are assigned inside the `if ngem:` block of the real script, as are the calls which use them.
NGEM_SCRIPT = """
ngem = False
recon = False
output = "/output"
ngem_path = "/path/to/ngem"

if ngem:
    start_tof = 20000  # start of the ToF range
    end_tof = 85000  # end of the ToF range
    bin_width = 10  # TOF bin width in us
    L = 56.4  # moderator to detector distance

    ws = LoadNGEM(Filename=file_list, BinWidth=bin_width, MinToF=start_tof, MaxToF=end_tof, PreserveEvents=False)
    MoveInstrumentComponent(ws, "source", X=0, Y=0, Z=-(pos[2] + L))
elif recon:
    reconstruct_tomo(dataset)
"""

NGEM_TOF_LINES = [
    "    start_tof = 20000  # start of the ToF range",
    "    end_tof = 85000  # end of the ToF range",
    "    bin_width = 10  # TOF bin width in us",
    "    L = 56.4  # moderator to detector distance",
]


def apply_to(script_value, job_inputs):
    """
    Apply the IMAT transform to a script and return the result.

    :param script_value: The script text to transform.
    :param job_inputs: The inputs of the job to transform for.
    :return: The transformed script text.
    """
    job = Mock()
    job.id = "job_test"
    job.inputs = job_inputs
    script = PreScript(value=script_value)
    with patch("fia_api.scripts.transforms.imat_transforms.DEV_MODE", False):
        IMATTransform().apply(script, job)
    return script.value


def test_imat_transform_sets_ngem_tof_parameters():
    """Test the reduction parameters from the specification replace the ones the script ships with"""
    inputs = {"ngem": "true", "start_tof": 15000, "end_tof": "90000", "bin_width": 5, "L": "58.25"}

    result = apply_to(NGEM_SCRIPT.strip(), inputs)

    for line in [
        "    start_tof = 15000  # start of the ToF range",
        "    end_tof = 90000  # end of the ToF range",
        "    bin_width = 5  # TOF bin width in us",
        "    L = 58.25  # moderator to detector distance",
    ]:
        assert line in result.splitlines()
    # The lines using the parameters, and the rest of the script, are left as the reduction ships them.
    assert "    ws = LoadNGEM(Filename=file_list, BinWidth=bin_width, MinToF=start_tof" in result
    assert 'MoveInstrumentComponent(ws, "source", X=0, Y=0, Z=-(pos[2] + L))' in result
    ast.parse(result)


def test_imat_transform_keeps_shipped_values_without_inputs():
    """Test a job without the reduction inputs keeps the values the script ships with, as a rerun does"""
    result = apply_to(NGEM_SCRIPT.strip(), {"ngem": "true"})

    for line in NGEM_TOF_LINES:
        assert line in result.splitlines()


def test_imat_transform_ignores_values_that_are_not_numbers():
    """Test a value which is not a number is left out of the script rather than written into it"""
    inputs = {"ngem": "true", "start_tof": "1; import os", "L": None}

    result = apply_to(NGEM_SCRIPT.strip(), inputs)

    for line in NGEM_TOF_LINES:
        assert line in result.splitlines()
    ast.parse(result)


@pytest.mark.parametrize(
    ("line", "inputs", "expected"),
    [
        ("    start_tof = 20000  # start", {"start_tof": 15000}, "    start_tof = 15000  # start"),
        ("\tL = 56.4", {"L": 58.0}, "\tL = 58"),
        ("L = 56.4  # distance", {"L": "55.75"}, "L = 55.75  # distance"),
        ("    bin_width = 10", {"bin_width": "2.5"}, "    bin_width = 2.5"),
        # Nothing to change when the job carries no input for the parameter, or a value which is not a number.
        ("    start_tof = 20000", {}, None),
        ("    start_tof = 20000", {"start_tof": "20 000"}, None),
        ("    L = 56.4", {"L": True}, None),
        ("    L = 56.4", {"L": float("inf")}, None),
        # Lines which only mention a parameter, or end in one of its names, are not assignments of it.
        ("    ws = LoadNGEM(BinWidth=bin_width, MinToF=start_tof)", {"start_tof": 1}, None),
        ("    TOTAL = 3", {"L": 1}, None),
        ("    Label = 'frame'", {"L": 1}, None),
        ("    # start_tof = 20000", {"start_tof": 1}, None),
    ],
)
def test_ngem_tof_assignment(line, inputs, expected):
    """Test only the assignment lines of the nGEM parameters are rewritten, and keep their indentation"""
    assert _ngem_tof_assignment(line, inputs, "job_test") == expected


def apply_transform_and_verify(job_inputs, expected_replacements, dev_mode=False):
    """Helper to apply transform and verify results against expected replacements in SCRIPT"""
    job = Mock()
    job.id = "job_test"
    job.inputs = job_inputs
    script = PreScript(value=SCRIPT.strip())
    with patch("fia_api.scripts.transforms.imat_transforms.DEV_MODE", dev_mode):
        IMATTransform().apply(script, job)

    expected_lines = SCRIPT.strip().splitlines()

    for old, new in expected_replacements.items():
        found = False
        for i, line in enumerate(expected_lines):
            if line.startswith(old):
                expected_lines[i] = new
                found = True
        if not found:
            # If not in SCRIPT but expected, it won't be in script.value either unless we add it
            pass

    assert script.value == "\n".join(expected_lines)


def test_imat_transform_all_inputs():
    """Test IMAT transform with all inputs provided"""
    inputs = {
        "runno": 99999,
        "images_dir": "/super/cool/path",
        "ngem_path": "/cycle/IMAT_2024_1/file.txt",
        "ngem": "true",
        "recon": "true",
    }
    replacements = {
        "runno =": "runno = 99999",
        "dataset_path =": 'dataset_path = "/super/cool/path"',
        "ngem_path =": 'ngem_path = "/cycle/IMAT_2024_1/file.txt"',
        "ngem =": "ngem = True",
        "recon =": "recon = True",
        "output =": 'output = "/cycle/IMAT_24_1_nxs"',
    }
    apply_transform_and_verify(inputs, replacements, dev_mode=False)


def test_imat_transform_prefers_published_ngem_output_path():
    """Test IMAT transform uses the output folder run-detection published rather than deriving one"""
    inputs = {
        "ngem_path": "/ngem/nGEM-INES/DATA/IMAT_2026_01/IMAT00038896",
        "ngem_output_path": "/ngem/nGEM-INES/DATA/IMAT_26_1_nxs",
        "ngem": "true",
    }
    replacements = {
        "ngem_path =": 'ngem_path = "/ngem/nGEM-INES/DATA/IMAT_2026_01/IMAT00038896"',
        "ngem =": "ngem = True",
        "output =": 'output = "/ngem/nGEM-INES/DATA/IMAT_26_1_nxs"',
    }
    apply_transform_and_verify(inputs, replacements, dev_mode=False)


def test_imat_transform_dev_mode():
    """Test IMAT transform when DEV_MODE is True"""
    inputs = {
        "ngem_path": "/new/ngem/path/file.txt",
    }
    replacements = {
        "ngem_path =": 'ngem_path = "/new/ngem/path/file.txt"',
        "ngem =": "ngem = False",
        "recon =": "recon = False",
        "output =": 'output = "/output"',
    }
    apply_transform_and_verify(inputs, replacements, dev_mode=True)


def test_imat_transform_defaults():
    """Test IMAT transform with default/false values for booleans and missing optional inputs"""
    inputs = {
        "ngem": "false",
        "recon": "false",
    }
    replacements = {
        "ngem =": "ngem = False",
        "recon =": "recon = False",
        "output =": 'output = "/output"',
    }
    apply_transform_and_verify(inputs, replacements)


def test_imat_transform_missing_booleans():
    """Test IMAT transform when boolean inputs are missing, they should default to False in script"""
    inputs = {}
    replacements = {
        "ngem =": "ngem = False",
        "recon =": "recon = False",
        "output =": 'output = "/output"',
    }
    apply_transform_and_verify(inputs, replacements)


def test_imat_transform_partial_inputs():
    """Test IMAT transform with some inputs provided and some missing"""
    inputs = {
        "runno": 12345,
        "ngem": "true",
    }
    replacements = {
        "runno =": "runno = 12345",
        "ngem =": "ngem = True",
        "recon =": "recon = False",
        "output =": 'output = "/output"',
    }
    apply_transform_and_verify(inputs, replacements)


@pytest.mark.parametrize(
    ("ngem_run_path", "expected"),
    [
        ("/ngem/nGEM-INES/DATA/IMAT_2026_01/IMAT00038896", "/ngem/nGEM-INES/DATA/IMAT_26_1_nxs"),
        ("/ngem/nGEM-INES/DATA/IMAT_2026_04/IMAT00040389", "/ngem/nGEM-INES/DATA/IMAT_26_4_nxs"),
        # The raw folder pads the cycle number, the reduced folder leaves two digit cycles alone.
        ("/ngem/nGEM-INES/DATA/IMAT_2026_10/IMAT00040389", "/ngem/nGEM-INES/DATA/IMAT_26_10_nxs"),
        ("/cycle/IMAT_2024_1/file.txt", "/cycle/IMAT_24_1_nxs"),
    ],
)
def test_ngem_output_path(ngem_run_path, expected):
    """Test _ngem_output_path maps a raw nGEM run folder to the reduced data folder of its cycle"""
    assert _ngem_output_path(ngem_run_path) == expected


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        ("ngem = True", True),
        ("recon = False\nngem = True\n", True),
        ('ngem = "true"', True),
        ("    ngem = True", True),
        ("ngem = False", False),
        ("recon = True", False),
        ("# ngem = True", False),
        ("ngem_paths = True", False),
        ("", False),
    ],
)
def test_script_is_ngem(script, expected):
    """Test script_is_ngem picks up the nGEM switch and nothing else"""
    assert script_is_ngem(script) is expected


def test_script_is_ngem_after_transform():
    """Test a script the transform has switched to nGEM is recognised as an nGEM script"""
    job = Mock()
    job.id = "job_test"
    job.inputs = {"ngem": "true", "recon": "false"}
    script = PreScript(value=SCRIPT.strip())
    with patch("fia_api.scripts.transforms.imat_transforms.DEV_MODE", False):
        IMATTransform().apply(script, job)

    assert script_is_ngem(script.value) is True
