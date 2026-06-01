"""Test Case for IMAT transforms"""

from unittest.mock import Mock, patch

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.imat_transforms import IMATTransform, _extract_cycle_details

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


def test_extract_cycle_details_standard():
    """Test _extract_cycle_details with a standard path format"""
    cycle_num, cycle_year = _extract_cycle_details("/some/path/IMAT_2024_1/file.txt")
    assert cycle_num == "1"
    assert cycle_year == "24"


def test_extract_cycle_details_different_year_and_cycle():
    """Test _extract_cycle_details with a different year and cycle format"""
    cycle_num, cycle_year = _extract_cycle_details("/data/IMAT_2023_02/data.nxs")
    assert cycle_num == "02"
    assert cycle_year == "23"


def test_extract_cycle_details_multiple_underscores():
    """Test _extract_cycle_details with multiple underscores in the path"""
    cycle_num, cycle_year = _extract_cycle_details("/path/to/some_folder/IMAT_2022_3/my_file_name.txt")
    assert cycle_num == "3"
    assert cycle_year == "22"
