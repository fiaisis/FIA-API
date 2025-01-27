"""
Test cases for LoqTransform
"""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.sans_transform import SansTransform


@pytest.fixture
def script():
    """
    LoqTransform  PreScript fixture
    :return:
    """
    return PreScript(
        value="""
import math
import numpy
import csv
import datetime

from mantid.kernel import ConfigService
from mantid.simpleapi import RenameWorkspace, SaveRKH, SaveNXcanSAS, GroupWorkspaces, mtd, ConjoinWorkspaces, SaveNexusProcessed
from mantid import config
from sans.user_file.toml_parsers.toml_reader import TomlReader
import sans.command_interface.ISISCommandInterface as ici

# Setup by rundetection
user_file = "/extras/sans2d/MaskFile.toml"
sample_scatter = 110754
sample_transmission = None
sample_direct = None
can_scatter = None
can_transmission = None
can_direct = None
sample_thickness = 1.0
sample_geometry = "Disc"
sample_height = 8.0
sample_width = 8.0
slice_wavs = [1.75, 2.75, 3.75, 4.75, 5.75, 6.75, 8.75, 10.75, 12.5]
phi_limits_list = [(-30, 30), (60, 120)]
"""
    )


@pytest.fixture
def reduction_1():
    """
    Reduction fixture
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "user_file": "/extras/sans2d/BestMaskFile.toml",
        "run_number": 10,
        "scatter_transmission": 9,
        "scatter_direct": 3,
        "can_scatter": 5,
        "can_transmission": 4,
        "can_direct": 3,
        "sample_thickness": 2.0,
        "sample_geometry": "Disc",
        "sample_height": 8.0,
        "sample_width": 8.0,
        "slice_wavs": "[1.0, 2.0, 3.0]",
        "phi_limits": "[(-20, 20), (30, 160)]",
    }
    mock.instrument.instrument_name = "SANS2D"
    return mock


@pytest.fixture
def reduction_2():
    """
    Reduction fixture
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "user_file": "/extras/sans2d/BestMaskFile.toml",
        "run_number": 5,
        "sample_thickness": 2.0,
        "sample_geometry": "Disc",
        "sample_height": 8.0,
        "sample_width": 8.0,
        "slice_wavs": "[1.0, 2.0, 3.0]",
        "phi_limits": "[(-20, 20), (30, 160)]",
    }
    mock.instrument.instrument_name = "SANS2D"
    return mock


def test_sans2d_transform_apply(script, reduction_1):
    """
    Test loq transform applies correct updates to script
    :param script: The script fixture
    :param reduction_1: The reduction fixture
    :return: None
    """
    transform = SansTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction_1)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)
    replacements = {
        "user_file": 'user_file = "/extras/sans2d/BestMaskFile.toml"',
        "sample_scatter": "sample_scatter = 10",
        "sample_transmission": "sample_transmission = 9",
        "sample_direct": "sample_direct = 3",
        "can_scatter": "can_scatter = 5",
        "can_transmission": "can_transmission = 4",
        "can_direct": "can_direct = 3",
        "sample_thickness": "sample_thickness = 2.0",
        "sample_geometry": 'sample_geometry = "Disc"',
        "sample_height": "sample_height = 8.0",
        "sample_width": "sample_width = 8.0",
        "slice_wavs": "slice_wavs = [1.0, 2.0, 3.0]",
        "phi_limits": "phi_limits_list = [(-20, 20), (30, 160)]",
    }

    for index, line in enumerate(updated_lines):
        for key, expected_line in replacements.items():
            if line.startswith(key):
                assert line == expected_line
                break
        else:
            assert line == original_lines[index]


def test_sans2d_transform_apply_with_optionals(script, reduction_2):
    """
    Test loq transform applies correct updates to script
    :param script: The script fixture
    :param reduction_2: The reduction fixture
    :return: None
    """
    transform = SansTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction_2)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)
    replacements = {
        "user_file": 'user_file = "/extras/sans2d/BestMaskFile.toml"',
        "sample_scatter": "sample_scatter = 5",
        "sample_transmission": "sample_transmission = None",
        "sample_direct": "sample_direct = None",
        "can_scatter": "can_scatter = None",
        "can_transmission": "can_transmission = None",
        "can_direct": "can_direct = None",
        "sample_thickness": "sample_thickness = 2.0",
        "sample_geometry": 'sample_geometry = "Disc"',
        "sample_height": "sample_height = 8.0",
        "sample_width": "sample_width = 8.0",
        "slice_wavs": "slice_wavs = [1.0, 2.0, 3.0]",
        "phi_limits": "phi_limits_list = [(-20, 20), (30, 160)]",
    }

    for index, line in enumerate(updated_lines):
        for key, expected_line in replacements.items():
            if line.startswith(key):
                assert line == expected_line
                break
        else:
            assert line == original_lines[index]
