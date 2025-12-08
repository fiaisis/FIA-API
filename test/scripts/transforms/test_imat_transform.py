"""Test Case for osiris transforms"""

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
"""


def test_iris_transform_spectroscopy():
    """Test spectroscopy transform"""
    expected_script = """
FILTERS = {f.__name__: f for f in load_filter_packages()}
RECON_DEFAULT_SETTINGS = {'algorithm': 'FBP_CUDA', 'filter_name': 'ram-lak', 'cor': 1, 'tilt': 0}
DEBUG = False
DEBUG_DIR = Path("/output/debug")


# To be edited by us for the script
runno = 99999
dataset_path = Path("/super/cool/path")"""
    job = Mock()
    job.inputs = {
        "runno": 99999,
        "images_dir": "/super/cool/path",
    }
    script = PreScript(value=SCRIPT)
    IMATTransform().apply(script, job)

    assert script.value == expected_script
