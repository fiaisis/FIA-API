"""
Tests for utility functions
"""

from pathlib import Path

import pytest
from fastapi import HTTPException

from fia_api.core.exceptions import UnsafePathError
from fia_api.core.utility import filter_script_for_tokens, forbid_path_characters, safe_check_filepath


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
    """
    Test the filter script for tokens
    """
    output_script = filter_script_for_tokens(input_script)

    assert output_script == expected_script


def test_safe_check_file_path(tmp_path):
    """
    Test no exceptions raised when checking a safe relative file path
    """
    base_path = Path(tmp_path / "folder")
    file_path = base_path / "file.txt"
    file_path.mkdir(parents=True, exist_ok=True)
    result = safe_check_filepath(file_path, base_path)
    # No exceptions raised
    assert result is None


def test_non_relative_file_path(tmp_path):
    """
    Tests non relative file path without trigerring FileNotFound
    """
    base_path = Path(tmp_path / "folder")
    file_path = tmp_path / "non_relative_folder" / "file.txt"
    file_path.mkdir(parents=True, exist_ok=True)
    with pytest.raises(HTTPException) as exc_info:
        safe_check_filepath(file_path, base_path)
    assert exc_info.errisinstance(HTTPException)
    assert "Invalid path being accessed" in exc_info.exconly()
    assert "and file not found" not in exc_info.exconly()


def test_non_existing_file_path(tmp_path):
    """
    Tests non relative and non existing file to see if FileNotFound logic is triggered
    """
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
