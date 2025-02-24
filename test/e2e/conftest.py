"""Global fixture for e2e tests"""

import pytest

# pylint: disable=wrong-import-order
from test.utils import setup_database

setup = False


@pytest.fixture(autouse=True)
def _setup(faker):
    """
    Setup database pre-testing
    :return:
    """
    # We require this horrible global setup as faker is a function scoped fixture and not a session scoped
    global setup  # noqa: PLW0603
    if not setup:
        setup_database(faker)
        setup = True
