"""This module provides a factory function to get the appropriate transform for a given instrument."""

import logging

from fia_api.scripts.transforms.enginx_transform import EnginxTransform
from fia_api.scripts.transforms.iris_transform import IrisTransform
from fia_api.scripts.transforms.mari_transforms import MariTransform
from fia_api.scripts.transforms.osiris_transform import OsirisTransform
from fia_api.scripts.transforms.output_transform import OutputTransform
from fia_api.scripts.transforms.sans_transform import SansTransform
from fia_api.scripts.transforms.test_transforms import TestTransform
from fia_api.scripts.transforms.tosca_transform import ToscaTransform
from fia_api.scripts.transforms.transform import MissingTransformError, Transform
from fia_api.scripts.transforms.vesuvio_transform import VesuvioTransform

logger = logging.getLogger(__name__)


def get_transform_for_instrument(instrument: str) -> Transform:  # noqa: PLR0911
    """
    Get the appropriate transform for the given instrument and run file
    :param instrument: str - the instrument
    :return: - Transform
    """
    logger.info("Getting transform for instrument: %s", instrument)
    match instrument.lower():
        case "mari":
            return MariTransform()
        case "tosca":
            return ToscaTransform()
        case "osiris":
            return OsirisTransform()
        case "loq" | "sans2d":
            return SansTransform()
        case "iris":
            return IrisTransform()
        case "vesuvio":
            return VesuvioTransform()
        case "enginx":
            return EnginxTransform()
        case "test":
            return TestTransform()
        case _:
            raise MissingTransformError(f"No transform for instrument {instrument}")
