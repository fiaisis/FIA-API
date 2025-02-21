"""Global fixture for e2e tests"""

import pytest

# pylint: disable=wrong-import-order
from test.utils import setup_database


@pytest.fixture(scope="session", autouse=True)
def _setup():
    """
    Setup database pre-testing
    :return:
    """
    setup_database()
