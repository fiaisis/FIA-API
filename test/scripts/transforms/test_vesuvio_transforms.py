"""Test cases for VesuvioTransform"""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.vesuvio_transform import VesuvioTransform


@pytest.fixture
def script():
    """
    VesuvioTransform  PreScript fixture
    :return:
    """
    return PreScript(
        value="""
# Setup by rundetection
ip = "IP0005.par"
empty_runs = "50309-50341"
runno = "52695"

# Default constants
filepath_ip = f"/extras/vesuvio/{ip}"
rebin_vesuvio_run_parameters = "50,1,500"
rebin_transmission_parameters="0.6,-0.05,1.e7"
crop_min = 10
crop_max = 400
back_scattering_spectra = "3-134"
forward_scattering_spectra = "135-182"
cache_location="/extras/vesuvio/cached_files/"
""")


@pytest.fixture
def reduction():
    """
    Reduction fixture
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "runno": "12345",
        "empty_runs": "12345-12355",
        "ip_file": "IP0001.par"
    }
    return mock


def test_vesuvio_transform_apply(script, reduction):
    """
    Test vesuvio transform applies correct updates to script
    :param script: The script fixture
    :param reduction: The reduction fixture
    :return: None
    """
    transform = VesuvioTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)
    for index, line in enumerate(updated_lines):
        if line.startswith("runno"):
            assert line == 'runno = "12345"'
        elif line.startswith("empty_runs"):
            assert line == 'empty_runs = "12345-12355"'
        elif line.startswith("ip"):
            assert line == 'ip = "IP0001.par"'
        else:
            assert line == original_lines[index]
