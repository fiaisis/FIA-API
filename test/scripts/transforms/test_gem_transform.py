"""Test cases for GEMTransform."""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.gem_transform import GEMTransform

SCRIPT = """
mode = "default_mode"
input_mode = "default_input_mode"
vanadium_runno = 0
runno = 0
calibration_dir = None
splined_vanadium_dir = "default_splined_vanadium_dir"
config_file = "default_config_file"
output_dir = "default_output_dir"
"""


@pytest.fixture
def base_job():
    """Fixture for base job inputs."""
    job = Mock()
    job.id = "test-job-gem"
    job.inputs = {
        "mode": "transmission",
        "input_mode": "raw",
        "calibration_dir": "/path/to/cal",
        "splined_vanadium_dir": "/path/to/splined",
        "config_file": "/path/to/config",
        "output_dir": "/path/to/output",
        "runno": 12345,
    }
    return job


@pytest.fixture
def create_expected_script():
    """Fixture returning a helper function to construct the expected script with runno."""

    def _create(runno_str: str) -> str:
        return f"""
mode = "transmission"
input_mode = "raw"
vanadium_runno = {runno_str}
runno = {runno_str}
calibration_dir = /path/to/cal
splined_vanadium_dir = "/path/to/splined"
config_file = "/path/to/config"
output_dir = "/path/to/output\""""

    return _create


def test_gem_transform_single_run(base_job, create_expected_script):
    """Test GEMTransform with a single run number."""
    script = PreScript(value=SCRIPT)
    GEMTransform().apply(script, base_job)

    assert script.value == create_expected_script("12345")


def test_gem_transform_contiguous_runs(base_job, create_expected_script):
    """Test GEMTransform with contiguous runs."""
    base_job.inputs["runno"] = [12345, 12346, 12347]
    script = PreScript(value=SCRIPT)
    GEMTransform().apply(script, base_job)

    assert script.value == create_expected_script("12345-12347")


def test_gem_transform_non_contiguous_runs(base_job, create_expected_script):
    """Test GEMTransform with non-contiguous runs."""
    base_job.inputs["runno"] = [12345, 12347, 12349]
    script = PreScript(value=SCRIPT)
    GEMTransform().apply(script, base_job)

    assert script.value == create_expected_script("12345,12347,12349")


def test_gem_transform_list_length_one(base_job, create_expected_script):
    """Test GEMTransform with list containing a single run."""
    base_job.inputs["runno"] = [12345]
    script = PreScript(value=SCRIPT)
    GEMTransform().apply(script, base_job)

    assert script.value == create_expected_script("12345")


def test_gem_transform_apply(base_job):
    """Test GEMTransform only modifies expected lines and leaves others unchanged."""
    transform = GEMTransform()
    script = PreScript(value=SCRIPT)
    original_lines = script.value.splitlines()

    transform.apply(script, base_job)

    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)

    for index, line in enumerate(updated_lines):
        if line.startswith("mode ="):
            assert line == 'mode = "transmission"'
        elif line.startswith("input_mode ="):
            assert line == 'input_mode = "raw"'
        elif line.startswith("vanadium_runno ="):
            assert line == "vanadium_runno = 12345"
        elif line.startswith("runno ="):
            assert line == "runno = 12345"
        elif line.startswith("calibration_dir ="):
            assert line == "calibration_dir = /path/to/cal"
        elif line.startswith("splined_vanadium_dir ="):
            assert line == 'splined_vanadium_dir = "/path/to/splined"'
        elif line.startswith("config_file ="):
            assert line == 'config_file = "/path/to/config"'
        elif line.startswith("output_dir = "):
            assert line == 'output_dir = "/path/to/output"'
        else:
            assert line == original_lines[index]
