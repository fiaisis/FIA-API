"""
Test cases for EnginxTransform
"""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.enginx_transform import EnginxTransform


@pytest.fixture
def script():
    """
    EnginxTransform PreScript fixture
    :return:
    """
    return PreScript(
        value="""# import mantid algorithms, numpy and matplotlib
from mantid.simpleapi import *
import matplotlib.pyplot as plt
import numpy as np
import os

from Engineering.EnginX import EnginX
from Engineering.EnggUtils import GROUP
CWDIR = "/output"
FULL_CALIB = os.path.join(CWDIR, "ENGINX_whole_inst_calib.nxs")

vanadium_run = "1" # this is instrument spec
focus_runs = ["1"] # this is the run number
ceria_run = "1" # Per experiment in instrument specification
group = GROUP["BOTH"] # in instrument spec

enginx = EnginX(
            vanadium_run=vanadium_run,
            focus_runs=focus_runs,
            save_dir=CWDIR,
            full_inst_calib_path=FULL_CALIB,
            ceria_run=ceria_run,
            group=GROUP.BOTH,
        )
enginx.main(plot_cal=False, plot_foc=False)
"""
    )


@pytest.fixture
def reduction():
    """
    Reduction fixture
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "vanadium_run": "654321",
        "ceria_run": "987654",
        "group": "BOTH",
    }
    mock.run = Mock()
    mock.run.filename = "ENGINX1234.nxs"
    return mock


@pytest.fixture
def reduction_with_prefix():
    """
    Reduction fixture with ENGINX prefix already in the run numbers
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "vanadium_run": "ENGINX654321",
        "ceria_run": "ENGINX987654",
        "group": "BOTH",
    }
    mock.id = "test-job-id-prefix"
    mock.run = Mock()
    mock.run.filename = "ENGINX1234.nxs"
    return mock


@pytest.fixture
def reduction_with_int_inputs():
    """
    Reduction fixture with integer vanadium and ceria runs
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "vanadium_run": 654321,
        "ceria_run": 987654,
        "group": "BOTH",
    }
    mock.run = Mock()
    mock.run.filename = "ENGINX1234.nxs"
    return mock


def test_enginx_transform_apply(script, reduction):
    """
    Test enginx transform applies correct updates to script
    :param script: The script fixture
    :param reduction: The reduction fixture
    :return: None
    """
    transform = EnginxTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    # Check that all instances of vanadium_run, focus_runs, ceria_run, and group are updated
    for index, line in enumerate(updated_lines):
        if (
            ("vanadium_run=" in line and 'vanadium_run="ENGINX654321"' not in line)
            or ("focus_runs=" in line and "focus_runs=['ENGINX1234']" not in line)
            or ("ceria_run=" in line and 'ceria_run="ENGINX987654"' not in line)
            or ("group=" in line and 'group=GROUP["BOTH"]' not in line)
        ):
            raise AssertionError(f"Line {index} not updated correctly: {line}")


def test_enginx_transform_apply_with_prefix(script, reduction_with_prefix):
    """
    Test enginx transform applies correct updates to script when prefix is already present
    :param script: The script fixture
    :param reduction_with_prefix: The reduction fixture with prefix
    :return: None
    """
    transform = EnginxTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction_with_prefix)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    # Check that all instances of vanadium_run, focus_runs, ceria_run, and group are updated
    for index, line in enumerate(updated_lines):
        if (
            ("vanadium_run=" in line and 'vanadium_run="ENGINX654321"' not in line)
            or ("focus_runs=" in line and "focus_runs=['ENGINX1234']" not in line)
            or ("ceria_run=" in line and 'ceria_run="ENGINX987654"' not in line)
            or ("group=" in line and 'group=GROUP["BOTH"]' not in line)
        ):
            raise AssertionError(f"Line {index} not updated correctly: {line}")


def test_enginx_transform_apply_with_int_inputs(script, reduction_with_int_inputs):
    """
    Test enginx transform applies correct updates to script when inputs are integers
    :param script: The script fixture
    :param reduction_with_prefix: The reduction fixture with prefix
    :return: None
    """
    transform = EnginxTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction_with_int_inputs)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    # Check that all instances of vanadium_run, focus_runs, ceria_run, and group are updated
    for index, line in enumerate(updated_lines):
        if (
            ("vanadium_run=" in line and 'vanadium_run="ENGINX654321"' not in line)
            or ("focus_runs=" in line and "focus_runs=['ENGINX1234']" not in line)
            or ("ceria_run=" in line and 'ceria_run="ENGINX987654"' not in line)
            or ("group=" in line and 'group=GROUP["BOTH"]' not in line)
        ):
            raise AssertionError(f"Line {index} not updated correctly: {line}")


def test_enginx_transform_with_string_focus_runs(script):
    """
    Test enginx transform handles string focus_runs correctly
    :param script: The script fixture
    :return: None
    """
    transform = EnginxTransform()

    mock = Mock()
    mock.inputs = {
        "vanadium_run": "654321",
        "focus_runs": "765432",
        "ceria_run": "987654",
        "group": "BOTH",
    }
    mock.id = "test-job-id-string"
    mock.run = Mock()
    mock.run.filename = "ENGINX1234.nxs"

    original_lines = script.value.splitlines()
    transform.apply(script, mock)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    # Check that all instances of vanadium_run, focus_runs, ceria_run, and group are updated
    for index, line in enumerate(updated_lines):
        if (
            ("vanadium_run=" in line and 'vanadium_run="ENGINX654321"' not in line)
            or ("focus_runs=" in line and "focus_runs=['ENGINX1234']" not in line)
            or ("ceria_run=" in line and 'ceria_run="ENGINX987654"' not in line)
            or ("group=" in line and 'group=GROUP["BOTH"]' not in line)
        ):
            raise AssertionError(f"Line {index} not updated correctly: {line}")
