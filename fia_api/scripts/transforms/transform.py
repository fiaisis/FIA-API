"""
This module provides an abstract base class for implementing transformations on a given script. These transformations
apply string manipulations on the script depending on the specific implementation. A custom exception is also defined
for cases where a required transform is missing.

Classes:
Transform (ABC): An abstract base class that defines the interface for applying transformations on a script.
MissingTransformError (Exception): A custom exception for handling cases where a required transform is missing.
"""

from abc import ABC, abstractmethod

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript


class Transform(ABC):
    """Transform applies a string manipulation on a given script depending on the implementation"""

    @abstractmethod
    def apply(self, script: PreScript, job: Job) -> str | None:
        """
        Apply the transform on the given script
        :param script: PreScript - the script to transform
        :param job: Job the job entity
        :return: str (in case of json output) or None
        """


class MissingTransformError(Exception):
    """
    MissingTransformError is a custom exception that is raised when a required transform is missing. This exception
    should be used to handle cases where a specific transform implementation is expected but not found.
    """
