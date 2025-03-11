"""Tests for utility functions"""

import shutil
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from fia_api.core.exceptions import UnsafePathError
from fia_api.core.utility import (
    GITHUB_PACKAGE_TOKEN,
    filter_script_for_tokens,
    find_file_experiment_number,
    find_file_instrument,
    find_file_user_number,
    forbid_path_characters,
    get_packages,
    safe_check_filepath,
    safe_check_filepath_plotting,
)

CEPH_DIR = Path(TemporaryDirectory().name)


@pytest.fixture(autouse=True)
def _setup_and_clean_temp_dir():
    CEPH_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(CEPH_DIR)


def dummy_string_arg_function(arg: str) -> str:
    """Dummy function for testing"""
    return arg


def test_forbid_path_characters_with_dot_raises():
    """
    Test raises when string contains dot
    :return: None
    """
    with pytest.raises(UnsafePathError):
        forbid_path_characters(dummy_string_arg_function)("foo.")


def test_forbid_path_characters_with_fslash_raises():
    """
    Test raises when string contains forward slash
    :return: None
    """
    with pytest.raises(UnsafePathError):
        forbid_path_characters(dummy_string_arg_function)("foo/bar")


def test_forbid_path_characters_with_bslash_raises():
    """
    Test raises when string contains back slash
    :return:
    """
    with pytest.raises(UnsafePathError):
        forbid_path_characters(dummy_string_arg_function)("foo/\\bar\\baz")


def test_no_raise_when_no_bad_characters():
    """
    Test no raise when no bad characters
    :return:
    """
    assert forbid_path_characters(dummy_string_arg_function)("hello") == "hello"


GHP_SCRIPT = (
    "from mantid.kernel import ConfigService\n"
    'ConfigService.Instance()["network.github.api_token"] = "ghp_random_token"'
    "\nfrom mantid.simpleapi import *"
)
SCRIPT = "from mantid.kernel import ConfigService\nfrom mantid.simpleapi import *"
EXPECTED_SCRIPT = "from mantid.kernel import ConfigService\nfrom mantid.simpleapi import *"


@pytest.mark.parametrize(
    ("input_script", "expected_script"),
    [(GHP_SCRIPT, EXPECTED_SCRIPT), (SCRIPT, EXPECTED_SCRIPT)],
)
def test_filter_script_for_tokens(input_script, expected_script):
    """Test the filter script for tokens"""
    output_script = filter_script_for_tokens(input_script)

    assert output_script == expected_script


def test_safe_check_file_path(tmp_path):
    """Test no exceptions raised when checking a safe relative file path"""
    base_path = Path(tmp_path / "folder")
    file_path = base_path / "file.txt"
    file_path.mkdir(parents=True, exist_ok=True)
    result = safe_check_filepath(file_path, base_path)
    # No exceptions raised
    assert result is None


def test_non_relative_file_path(tmp_path):
    """Tests non relative file path without trigerring FileNotFound"""
    base_path = Path(tmp_path / "folder")
    file_path = tmp_path / "non_relative_folder" / "file.txt"
    file_path.mkdir(parents=True, exist_ok=True)
    with pytest.raises(HTTPException) as exc_info:
        safe_check_filepath(file_path, base_path)
    assert exc_info.errisinstance(HTTPException)
    assert "Invalid path being accessed" in exc_info.exconly()
    assert "and file not found" not in exc_info.exconly()


def test_non_existing_file_path(tmp_path):
    """Tests non relative and non existing file to see if FileNotFound logic is triggered"""
    base_path = Path(tmp_path / "folder")
    file_path = tmp_path / "non_relative_folder" / "file.txt"
    with pytest.raises(HTTPException) as exc_info:
        safe_check_filepath(file_path, base_path)
    assert exc_info.errisinstance(HTTPException)
    assert "Invalid path being accessed and file not found" in exc_info.exconly()


# Potentially redundant test as the previous test eventually hits this case
def test_non_existing_folder_path(tmp_path):
    """
    Tests non file path to triggering file not found.
    To run safe_check_filepath without the recursive call.
    """
    base_path = Path(tmp_path / "folder")
    file_path = tmp_path / "non_relative_folder"
    with pytest.raises(HTTPException) as exc_info:
        safe_check_filepath(file_path, base_path)
    assert exc_info.errisinstance(HTTPException)
    assert "Invalid path being accessed and file not found" in exc_info.exconly()


def test_get_packages():
    """Test the get_packages() function for a successful API call."""
    mock_response_data = [
        {
            "id": 294659748,
            "metadata": {"package_type": "container", "container": {"tags": ["6.11.0"]}},
        },
        {
            "id": 265303494,
            "metadata": {"package_type": "container", "container": {"tags": ["6.10.0"]}},
        },
        {
            "id": 220505057,
            "metadata": {"package_type": "container", "container": {"tags": ["6.9.1"]}},
        },
        {
            "id": 220504408,
            "metadata": {"package_type": "container", "container": {"tags": ["6.9.0"]}},
        },
        {
            "id": 220503717,
            "metadata": {"package_type": "container", "container": {"tags": ["6.8.0"]}},
        },
    ]

    with patch("fia_api.core.utility.requests.get") as mock_get:
        mock_get.return_value.status_code = HTTPStatus.OK
        mock_get.return_value.json.return_value = mock_response_data

        package_data = get_packages(org="fiaisis", image_name="mantid")
        assert package_data == mock_response_data

        # Verify the request was made with the correct URL and headers
        mock_get.assert_called_once_with(
            "https://api.github.com/orgs/fiaisis/packages/container/mantid/versions",
            headers={"Authorization": f"Bearer {GITHUB_PACKAGE_TOKEN}"},
            timeout=10,
        )


def test_get_packages_error():
    """Test the get_packages() function for an unsuccessful API call."""
    with patch("fia_api.core.utility.requests.get") as mock_get:
        mock_get.return_value.status_code = HTTPStatus.NOT_FOUND

        with pytest.raises(HTTPException) as excinfo:
            get_packages(org="fiaisis", image_name="mantid")

        assert excinfo.value.status_code == HTTPStatus.NOT_FOUND

        # Verify the request was made with the correct URL and headers
        mock_get.assert_called_once_with(
            "https://api.github.com/orgs/fiaisis/packages/container/mantid/versions",
            headers={"Authorization": f"Bearer {GITHUB_PACKAGE_TOKEN}"},
            timeout=10,
        )


def test_get_packages_forbidden_invalid_token():
    """Test the get_packages() function for a forbidden API call caused by an invalid Bearer token."""
    invalid_token = "invalid_token_value"  # noqa: S105

    with patch("fia_api.core.utility.requests.get") as mock_get:
        mock_get.return_value.status_code = HTTPStatus.FORBIDDEN

        with patch("fia_api.core.utility.GITHUB_PACKAGE_TOKEN", invalid_token):
            with pytest.raises(HTTPException) as excinfo:
                get_packages(org="fiaisis", image_name="mantid")

            assert excinfo.value.status_code == HTTPStatus.FORBIDDEN

            # Verify the request was made with the incorrect token
            mock_get.assert_called_once_with(
                "https://api.github.com/orgs/fiaisis/packages/container/mantid/versions",
                headers={"Authorization": f"Bearer {invalid_token}"},
                timeout=10,
            )


@pytest.mark.parametrize(
    ("filepath_to_check", "result"),
    [
        (Path(CEPH_DIR) / "good" / "path" / "here" / "file.txt", True),
        (Path(CEPH_DIR) / "bad" / "path" / "here" / "file.txt", False),
        (Path(CEPH_DIR) / ".." / ".." / ".." / "file.txt", False),
    ],
)
def test_safe_check_filepath_plotting(filepath_to_check: Path, result: bool):
    if result:
        filepath_to_check.parent.mkdir(parents=True, exist_ok=True)
        filepath_to_check.write_text("Hello World!")
        safe_check_filepath_plotting(filepath_to_check, str(CEPH_DIR))
    else:
        with pytest.raises((HTTPException, FileNotFoundError)):
            safe_check_filepath_plotting(filepath_to_check, str(CEPH_DIR))


def test_find_instrument_most_likely_file():
    with TemporaryDirectory() as tmpdir:
        instrument_name = "FUN_INST"
        experiment_number = 1231234
        filename = "MAR1912991240_asa_dasd_123.nxspe"
        path = Path(tmpdir) / instrument_name / "RBNumber" / f"RB{experiment_number}" / "autoreduced" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Hello World!")

        found_file = find_file_instrument(tmpdir, instrument_name, experiment_number, filename)

        assert found_file == path


@pytest.mark.parametrize(
    ("find_file_method", "method_inputs", "path_to_make"),
    [
        (
            find_file_instrument,
            {
                "ceph_dir": CEPH_DIR,
                "instrument": "FUN_INST",
                "experiment_number": 1231234,
                "filename": "MAR1912991240_asa_dasd_123.nxspe",
            },
            CEPH_DIR / "FUN_INST" / "RBNumber" / "RB1231234" / "autoreduced" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
        (
            find_file_experiment_number,
            {"ceph_dir": CEPH_DIR, "experiment_number": 1231234, "filename": "MAR1912991240_asa_dasd_123.nxspe"},
            CEPH_DIR / "GENERIC" / "autoreduce" / "ExperimentNumbers" / "1231234" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
        (
            find_file_user_number,
            {"ceph_dir": CEPH_DIR, "user_number": 1231234, "filename": "MAR1912991240_asa_dasd_123.nxspe"},
            CEPH_DIR / "GENERIC" / "autoreduce" / "UserNumbers" / "1231234" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
    ],
)
def test_find_file_method_in_a_dir(find_file_method: Callable, method_inputs: dict[str, Any], path_to_make: Path):
    with TemporaryDirectory() as tmpdir:
        instrument_name = "FUN_INST"
        experiment_number = 1231234
        filename = "MAR1912991240_asa_dasd_123.nxspe"
        path = (
            Path(tmpdir)
            / instrument_name
            / "RBNumber"
            / f"RB{experiment_number}"
            / "autoreduced"
            / "run-123141"
            / filename
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Hello World!")

        found_file = find_file_instrument(tmpdir, instrument_name, experiment_number, filename)

        assert found_file == path


@pytest.mark.parametrize(
    ("find_file_method", "method_inputs", "path_to_make"),
    [
        (
            find_file_instrument,
            {
                "ceph_dir": CEPH_DIR,
                "instrument": "FUN_INST",
                "experiment_number": 1231234,
                "filename": "MAR1912991240_asa_dasd_123.nxspe",
            },
            CEPH_DIR / "FUN_INST" / "RBNumber" / "RB1231234" / "autoreduced" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
        (
            find_file_experiment_number,
            {"ceph_dir": CEPH_DIR, "experiment_number": 1231234, "filename": "MAR1912991240_asa_dasd_123.nxspe"},
            CEPH_DIR / "GENERIC" / "autoreduce" / "ExperimentNumbers" / "1231234" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
        (
            find_file_user_number,
            {"ceph_dir": CEPH_DIR, "user_number": 1231234, "filename": "MAR1912991240_asa_dasd_123.nxspe"},
            CEPH_DIR / "GENERIC" / "autoreduce" / "UserNumbers" / "1231234" / "MAR1912991240_asa_dasd_123.nxspe",
        ),
    ],
)
def test_find_file_method_when_failed(find_file_method: Callable, method_inputs: dict[str, Any], path_to_make: Path):
    path_to_make.parent.mkdir(parents=True, exist_ok=True)

    found_file = find_file_method(**method_inputs)

    assert found_file is None


@pytest.mark.parametrize(
    ("find_file_method", "method_inputs"),
    [
        (find_file_instrument, {CEPH_DIR, "~/.ssh", "id_rsa", "MAR1912991240_asa_dasd_123.nxspe"}),
        (find_file_experiment_number, {CEPH_DIR, "~/.ssh", "id_rsa"}),
        (find_file_user_number, {CEPH_DIR, "~/.ssh", "id_rsa"}),
    ],
)
def test_find_file_methods_does_not_allow_path_injection(find_file_method: Callable, method_inputs: dict[str, Any]):
    with pytest.raises(HTTPException):
        find_file_method(*method_inputs)
