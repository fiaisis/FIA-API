"""
Inegration tests for data access.
Requires postgres running with user postgres and password password
Tests designed to test every specification with it's respective repo
with a live db connection
"""

import os
import datetime
from typing import Generator
from unittest import mock
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select, create_engine, NullPool
from sqlalchemy.orm import sessionmaker, Session

from fia_api.core.models import Base, Instrument, Job, JobOwner, JobType, Run, Script, State
from fia_api.core.repositories import ENGINE, SESSION, Repo, ensure_db_connection
from fia_api.core.specifications.job import JobSpecification


DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_IP = os.environ.get("DB_IP", "localhost")
DB_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:5432/fia"
TEST_JOB_OWNER = JobOwner(experiment_number=1)
TEST_JOB_OWNER_2 = JobOwner(experiment_number=2)
TEST_INSTRUMENT_1 = Instrument(instrument_name="instrument 1", latest_run=1, specification={"foo": "bar"})
TEST_INSTRUMENT_2 = Instrument(instrument_name="instrument 2", latest_run=1, specification={"foo": "bar"})
TEST_SCRIPT = Script(script="print('Script 1')", sha="some_sha", script_hash="some_hash")
TEST_JOB = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER,
    state=State.NOT_STARTED,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT_1,
    job_type=JobType.AUTOREDUCTION,
)
TEST_JOB_2 = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER_2,
    state=State.UNSUCCESSFUL,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT_1,
    job_type=JobType.AUTOREDUCTION,
)
TEST_JOB_3 = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER,
    state=State.NOT_STARTED,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT_2,
    job_type=JobType.AUTOREDUCTION,
)
TEST_RUN_1 = Run(
    filename="test_run",
    owner=TEST_JOB_OWNER,
    title="Test Run",
    users="User1, User2",
    run_start=datetime.datetime.now(datetime.UTC),
    run_end=datetime.datetime.now(datetime.UTC),
    good_frames=200,
    raw_frames=200,
    instrument=TEST_INSTRUMENT_1,
)
TEST_RUN_1.jobs.append(TEST_JOB)
TEST_RUN_2 = Run(
    filename="test_run",
    owner=TEST_JOB_OWNER_2,
    title="A Test Run 2",
    users="User1, User2",
    run_start=datetime.datetime.now(datetime.UTC),
    run_end=datetime.datetime.now(datetime.UTC),
    good_frames=100,
    raw_frames=200,
    instrument=TEST_INSTRUMENT_1,
)
TEST_RUN_2.jobs.append(TEST_JOB_2)
TEST_RUN_3 = Run(
    filename="test_run",
    owner=TEST_JOB_OWNER_2,
    title="Test Run 3",
    users="User1, User2",
    run_start=datetime.datetime.now(datetime.UTC),
    run_end=datetime.datetime.now(datetime.UTC),
    good_frames=100,
    raw_frames=200,
    instrument=TEST_INSTRUMENT_2,
)
TEST_RUN_3.jobs.append(TEST_JOB_3)


@pytest.fixture(scope="module", autouse=True)
def _setup() -> None:
    """
    Set up the test database before module
    :return: None
    """
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)

    with SESSION() as session:
        session.add(TEST_SCRIPT)
        session.add(TEST_INSTRUMENT_1)
        session.add(TEST_INSTRUMENT_2)
        session.add(TEST_RUN_1)
        session.add(TEST_RUN_2)
        session.add(TEST_RUN_3)
        session.add(TEST_JOB)
        session.commit()
        session.refresh(TEST_SCRIPT)
        session.refresh(TEST_INSTRUMENT_1)
        session.refresh(TEST_INSTRUMENT_2)
        session.refresh(TEST_RUN_1)
        session.refresh(TEST_RUN_2)
        session.refresh(TEST_RUN_3)


@pytest.fixture
def job_repo(session: Session) -> Repo[Job]:
    """
    JobRepo fixture
    :return: JobRepo
    """
    return Repo(session)


@pytest.fixture
def run_repo(session: Session) -> Repo[Run]:
    """
    RunRepo fixture
    :return: RunRepo
    """
    return Repo(session)


@pytest.fixture
def owner_repo(session: Session) -> Repo[JobOwner]:
    """
    JobOwnerRepo fixture.
    :return: JobOwnerRepo
    """
    return Repo(session)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DB_URL, poolclass=NullPool) # Test DB URL, what is this???
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine) -> Generator[Session, None, None]:
    """
    Session fixture
    :return: Session object
    """
    SessionLocal = sessionmaker(bind=engine, class_=Session)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.parametrize(
    ("order_field", "expected_ascending"),
    [
        ("run_start", [TEST_JOB, TEST_JOB_2]),
        ("run_end", [TEST_JOB, TEST_JOB_2]),
        ("experiment_number", [TEST_JOB, TEST_JOB_2]),
        ("experiment_title", [TEST_JOB_2, TEST_JOB]),
    ],
)
def test_jobs_by_instrument_sort_by_run_field(job_repo, order_field, expected_ascending):
    """Test jobs by run fields"""
    expected = expected_ascending
    result = job_repo.find(
        JobSpecification().by_instruments(["instrument 1"], order_by=order_field, order_direction="asc")
    )
    assert expected == result
    result = job_repo.find(
        JobSpecification().by_instruments(["instrument 1"], order_by=order_field, order_direction="desc")
    )
    expected.reverse()
    assert expected == result


def test_jobs_by_instrument_sort_by_job_field(job_repo):
    """Test sorting by job field"""
    result = job_repo.find(JobSpecification().by_instruments(["instrument 1"], order_by="state", order_direction="asc"))
    expected = [TEST_JOB_2, TEST_JOB]
    assert result == expected

    result = job_repo.find(
        JobSpecification().by_instruments(["instrument 1"], order_by="state", order_direction="desc")
    )
    expected.reverse()
    assert result == expected


@mock.patch("fia_api.core.repositories.select")
def test_ensure_db_connection_raises_httpexception(mock_select):
    """Test exception raised when runtime error occurs"""
    mock_session_object = MagicMock()
    mock_session_object.__enter__.return_value = mock_session_object

    ensure_db_connection(mock_session_object)

    mock_session_object.execute.assert_called_once_with(mock_select.return_value)


def test_add_one(owner_repo):
    """Test adding an entity"""
    experiment_number = -420
    owner_repo.add_one(JobOwner(experiment_number=experiment_number))
    with SESSION() as session:
        job_owner = (
            session.execute(select(JobOwner).where(JobOwner.experiment_number == experiment_number))
            .unique()
            .scalars()
            .one()
        )
        assert job_owner.experiment_number == experiment_number


def test_ensure_db_connection_with_real_session(session):
    """Test the ensure_db_connection method from repositories.py"""
    ensure_db_connection(session)