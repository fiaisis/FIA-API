"""
Tests for the transform factory function
"""

import pytest

from fia_api.scripts.transforms.factory import get_transform_for_instrument
from fia_api.scripts.transforms.iris_transform import IrisTransform
from fia_api.scripts.transforms.mari_transforms import MariTransform
from fia_api.scripts.transforms.osiris_transform import OsirisTransform
from fia_api.scripts.transforms.test_transforms import TestTransform
from fia_api.scripts.transforms.tosca_transform import ToscaTransform
from fia_api.scripts.transforms.transform import MissingTransformError


@pytest.mark.parametrize(
    "name,expected_transform",  # noqa: PT006
    [
        ("mari", MariTransform),
        ("tosca", ToscaTransform),
        ("test", TestTransform),
        ("osiris", OsirisTransform),
        ("iris", IrisTransform),
    ],
)
def test_transform_factory(name, expected_transform):
    """Parametrised factory tests"""
    assert isinstance(get_transform_for_instrument(name), expected_transform)


def test_get_transform_for_run_unknown_instrument():
    """
    Test that missing transform error raised for unknown instrument
    :return: None
    """
    instrument = "unknown"
    with pytest.raises(MissingTransformError) as excinfo:
        get_transform_for_instrument(instrument)
    assert str(excinfo.value) == f"No transform for instrument {instrument}"
