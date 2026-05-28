"""Test Case for IMAT transforms"""

from unittest.mock import Mock

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.imat_transforms import IMATTransform

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
    from unittest.mock import patch
    job = Mock()
    job.id = "job_test"
    job.inputs = job_inputs
    script = PreScript(value=SCRIPT.strip())
    with patch("fia_api.fia_api.DEV_MODE", dev_mode):
        IMATTransform().apply(script, job)

    actual_lines = script.value.splitlines()
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
        "ngem_path": "/new/ngem/path/file.txt",
        "ngem": "true",
        "recon": "true",
    }
    replacements = {
        "runno =": "runno = 99999",
        "dataset_path =": 'dataset_path = "/super/cool/path"',
        "ngem_path =": 'ngem_path = "/new/ngem/path/file.txt"',
        "ngem =": "ngem = True",
        "recon =": "recon = True",
        "output =": 'output = "/new/ngem/path"',
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
