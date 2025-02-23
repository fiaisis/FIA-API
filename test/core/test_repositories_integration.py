"""
Inegration tests for data access.
Requires postgres running with user postgres and password password
Tests designed to test every specification with it's respective repo
with a live db connection
"""

import datetime
from unittest import mock
from unittest.mock import Mock

import pytest
from db.data_models import Base, Instrument, Job, JobOwner, JobType, Run, Script, State

from fia_api.core.repositories import ENGINE, SESSION, Repo, test_connection
from fia_api.core.specifications.job import JobSpecification

TEST_JOB_OWNER = JobOwner(experiment_number=1)
TEST_JOB_OWNER_2 = JobOwner(experiment_number=2)
TEST_INSTRUMENT_1 = Instrument(instrument_name="instrument 1", latest_run=1, specification={"foo": "bar"})
TEST_INSTRUMENT_2 = Instrument(instrument_name="instrument 2", latest_run=1, specification={"foo": "bar"})
TEST_SCRIPT = Script(script="print('Script 1')", sha="some_sha", script_hash="some_hash")
TEST_JOB = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER_2,
    state=State.NOT_STARTED,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT_1,
    job_type=JobType.AUTOREDUCTION,
)
TEST_JOB_2 = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER,
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


@pytest.fixture()
def job_repo() -> Repo[Job]:
    """
    JobRepo fixture
    :return: JobRepo
    """
    return Repo()


@pytest.fixture()
def run_repo() -> Repo[Run]:
    """
    RunRepo fixture
    :return: RunRepo
    """
    return Repo()


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

    result = job_repo.find(JobSpecification().by_instruments(["instrument 1"], order_by="state", order_direction="desc"))
    expected.reverse()
    assert result == expected


@mock.patch("fia_api.core.repositories.SESSION")
@mock.patch("fia_api.core.repositories.select")
def test_test_connection_raises_httpexception(mock_select, mock_session):
    """Test exception raised when runtime error occurs"""
    mock_session_object = Mock()
    mock_session.return_value.__enter__.return_value = mock_session_object

    test_connection()
    mock_session_object.execute.assert_called_once_with(mock_select.return_value)
