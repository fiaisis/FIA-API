"""Global fixture for e2e tests"""

import os

import pytest
from sqlalchemy.orm import make_transient

from fia_api.core.repositories import SESSION
from test.e2e.constants import TEST_INSTRUMENT, TEST_JOB, TEST_RUN, TEST_SCRIPT
from test.utils import setup_database

setup = False

os.environ["FIA_API_API_KEY"] = "shh"


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


@pytest.fixture
def _user_owned_data_setup() -> None:
    """
    Set up the test database before module
    :return: None
    """
    with SESSION() as session:
        session.add(TEST_SCRIPT)
        session.add(TEST_INSTRUMENT)
        session.add(TEST_RUN)
        session.add(TEST_JOB)
        session.commit()
        session.refresh(TEST_SCRIPT)
        session.refresh(TEST_INSTRUMENT)
        session.refresh(TEST_RUN)
    yield
    with SESSION() as session:
        session.delete(TEST_RUN)
        session.delete(TEST_SCRIPT)
        session.delete(TEST_INSTRUMENT)
        session.delete(TEST_JOB)
        session.commit()
        session.flush()
        make_transient(TEST_RUN)
        make_transient(TEST_SCRIPT)
        make_transient(TEST_INSTRUMENT)
        make_transient(TEST_JOB)
