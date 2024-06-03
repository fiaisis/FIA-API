"""
Tests for utility functions
"""

import pytest

from fia_api.core.exceptions import UnsafePathError
from fia_api.core.utility import forbid_path_characters, filter_script_for_tokens


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


ghp_script = ("from mantid.kernel import ConfigService\n"
              "ConfigService.Instance()[\"network.github.api_token\"] = \"ghp_random_token\""
              "\nfrom mantid.simpleapi import *")
script = ("from mantid.kernel import ConfigService"
          "\nfrom mantid.simpleapi import *")
expected_script = ("from mantid.kernel import ConfigService"
                   "\nfrom mantid.simpleapi import *")


@pytest.mark.parametrize("input_script,expected_script", [(ghp_script, expected_script), (script, expected_script)])
def test_filter_script_for_tokens(input_script, expected_script):
    output_script = filter_script_for_tokens(input_script)

    assert output_script == expected_script
