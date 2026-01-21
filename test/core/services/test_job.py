"""Tests for job service"""

from unittest.mock import ANY, Mock, patch

import faker.generator
import pytest

from fia_api.core.exceptions import AuthError, MissingRecordError
from fia_api.core.models import Instrument, JobOwner, JobType, Run, Script, State
from fia_api.core.request_models import AutoreductionRequest
from fia_api.core.services.job import (
    count_jobs,
    count_jobs_by_instrument,
    create_autoreduction_job,
    get_all_jobs,
    get_experiment_number_for_job_id,
    get_job_by_id,
    get_job_by_instrument,
    list_mantid_runners,
    update_job_by_id,
)


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_jobs_by_instrument(mock_spec_class, mock_repo):
    """
    Test that get_jobs by instrument makes correct repo call
    :param mock_repo: Mocked Repo class
    :return: None
    """
    spec = mock_spec_class.return_value
    get_job_by_instrument("test", limit=5, offset=6)

    mock_repo.find.assert_called_once_with(spec.by_instruments(["test"], limit=5, offset=6))


@patch("fia_api.core.services.job._JOB_REPO")
def test_get_job_by_id_job_exists(mock_repo):
    """
    Test that correct repo call and return is made
    :param mock_repo: Mocked Repo
    :return:
    """
    expected_job = Mock()
    mock_repo.find_one.return_value = expected_job
    job = get_job_by_id(1)
    assert job == expected_job


@patch("fia_api.core.services.job._JOB_REPO")
def test_get_job_by_id_not_found_raises(mock_repo):
    """
    Test MissingRecordError raised when repo returns None
    :param mock_repo: Mocked Repo
    :return: None
    """
    mock_repo.find_one.return_value = None
    with pytest.raises(MissingRecordError):
        get_job_by_id(1)


@patch("fia_api.core.services.job._JOB_REPO")
def test_count_jobs(mock_repo):
    """
    Test count is called
    :return: None
    """
    count_jobs()
    mock_repo.count.assert_called_once()


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_count_jobs_by_instrument(mock_spec_class, mock_repo):
    """
    Test count by instrument
    :param mock_repo: mock repo fixture
    :return: None
    """
    spec = mock_spec_class.return_value
    count_jobs_by_instrument("TEST", filters={})
    mock_repo.count.assert_called_once_with(spec.by_instruments(["TEST"]))


@patch("fia_api.core.services.job.get_packages")
def test_list_mantid_runners_filters_empty_tags(mock_get_packages):
    mock_get_packages.return_value = [
        {"name": "sha256:aaa", "metadata": {"container": {"tags": ["6.8.0"]}}},
        {"name": "sha256:bbb", "metadata": {"container": {"tags": []}}},
        {"name": "sha256:ccc", "metadata": {"container": {}}},
        {"name": "sha256:ddd"},
    ]

    assert list_mantid_runners() == {"sha256:aaa": "6.8.0"}
    mock_get_packages.assert_called_once_with(org="fiaisis", image_name="mantid")


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_no_experiments(mock_get_exp, mock_repo):
    """Test get_job_by_id when no experiments are permitted"""
    job = Mock()
    job.owner = Mock()
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = []

    with pytest.raises(AuthError):
        get_job_by_id(1, user_number=1234)


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_with_experiments(mock_get_exp, mock_repo):
    """Test get_job_by_id_"""
    job = Mock()
    job.owner.experiment_number = 1234
    job.runs = [job, Mock()]
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = [1234]

    assert get_job_by_id(1, 1234) == job


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_job_by_id_for_user_with_user_number(mock_get_exp, mock_repo):
    """Test get_job_by_id_"""
    job = Mock()
    job.owner.user_number = 1234
    job.runs = [job, Mock()]
    mock_repo.find_one.return_value = job
    mock_get_exp.return_value = [1234]

    assert get_job_by_id(1, 1234) == job


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_without_user(mock_spec_class, mock_repo):
    """Test get_all_jobs without a user number"""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=10, offset=5, order_by="end", order_direction="asc")
    spec.all.assert_called_once_with(limit=10, offset=5, order_by="end", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_all_jobs_with_user_having_access(mock_get_experiments, mock_spec_class, mock_repo):
    """Test get_all_jobs with a user number and the user has access to experiments"""
    mock_get_experiments.return_value = [123, 456]
    spec = mock_spec_class.return_value
    get_all_jobs(user_number=1234, limit=5, offset=0, order_by="start", order_direction="desc")
    mock_get_experiments.assert_called_once_with(1234)
    spec.by_experiment_numbers.assert_called_once_with(
        [123, 456], limit=5, offset=0, order_by="start", order_direction="desc"
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
def test_get_all_jobs_with_user_no_access(mock_get_experiments, mock_spec_class, mock_repo):
    """Test get_all_jobs with a user number but no access to any experiments"""
    mock_repo.find.return_value = []
    mock_get_experiments.return_value = []
    spec = mock_spec_class.return_value
    jobs = get_all_jobs(user_number=9876)
    mock_get_experiments.assert_called_once_with(9876)
    spec.by_experiment_numbers.assert_called_once_with(
        [], order_by="start", order_direction="desc", limit=100, offset=0
    )
    mock_repo.find.assert_called_once_with(spec.by_experiment_numbers())
    assert jobs == []


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_experiment_number_from_job_id(mock_spec_class, mock_repo):
    job_id = faker.generator.random.randint(1, 1000)

    get_experiment_number_for_job_id(job_id)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class().by_id())


@patch("fia_api.core.services.job._JOB_REPO")
def test_get_experiment_number_from_job_id_expect_raise(mock_repo):
    job_id = faker.generator.random.randint(1, 1000)
    mock_repo.find_one.return_value = None

    with patch("fia_api.core.services.job.JobSpecification"), pytest.raises(ValueError):  # noqa: PT011
        get_experiment_number_for_job_id(job_id)


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_order_by_run_start_desc(mock_spec_class, mock_repo):
    """Test get_all_jobs with order_by 'run_start' in descending order."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0, order_by="run_start", order_direction="desc")
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="run_start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_order_by_run_start_asc(mock_spec_class, mock_repo):
    """Test get_all_jobs with order_by 'run_start' in ascending order."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0, order_by="run_start", order_direction="asc")
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="run_start", order_direction="asc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_default_order_by_start(mock_spec_class, mock_repo):
    """
    Test get_all_jobs without specifying a different order_by, per the function signature it should order by 'start'.
    """
    spec = mock_spec_class.return_value
    get_all_jobs(limit=5, offset=0)
    spec.all.assert_called_once_with(limit=5, offset=0, order_by="start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_get_all_jobs_with_pagination(mock_spec_class, mock_repo):
    """Test get_all_jobs with custom pagination (limit and offset)."""
    spec = mock_spec_class.return_value
    get_all_jobs(limit=15, offset=30)
    spec.all.assert_called_once_with(limit=15, offset=30, order_by="start", order_direction="desc")
    mock_repo.find.assert_called_once_with(spec.all())


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id(mock_spec_class, mock_repo):
    """Test update_job_by_id with valid job data."""
    job_id = 1
    job_data = Mock()  # This represents the JobResponse object
    job_data.state = State.SUCCESSFUL
    job_data.end = "2023-10-10T10:00:00"
    job_data.status_message = "Job completed successfully"
    job_data.outputs = {"output_key": "output_value"}
    job_data.stacktrace = None

    original_job = Mock()
    # the mocking library will create a new mock if we don't do this.
    original_job.stacktrace = None
    mock_repo.find_one.return_value = original_job

    update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    assert original_job.state == State.SUCCESSFUL
    assert original_job.end == "2023-10-10T10:00:00"
    assert original_job.status_message == "Job completed successfully"
    assert original_job.outputs == {"output_key": "output_value"}
    assert original_job.stacktrace is None
    mock_repo.update_one.assert_called_once_with(original_job)


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id_invalid_job_id(mock_spec_class, mock_repo):
    """Test update_job_by_id when the job ID does not exist."""
    job_id = 999
    job_data = Mock()
    mock_repo.find_one.return_value = None  # Simulate job not found

    with pytest.raises(MissingRecordError):
        update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    mock_repo.update_one.assert_not_called()


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job.JobSpecification")
def test_update_job_by_id_never_updates_certain_fields(mock_spec_class, mock_repo):
    """Test update_job_by_id ensuring certain fields are never updated"""
    job_id = 2
    job_data = Mock()
    job_data.state = State.NOT_STARTED
    job_data.start = "2023-10-09T12:00:01"
    job_data.status_message = "Job is running"
    job_data.input = None  # input should never be updated
    job_data.stacktrace = "Some stacktrace info"

    original_job = Mock()
    original_job.start = "2023-10-09T12:00:00"
    original_job.input = {"output_key": "previous_output"}

    mock_repo.find_one.return_value = original_job

    update_job_by_id(job_id, job_data)

    mock_spec_class.assert_called_once_with()
    mock_spec_class.return_value.by_id.assert_called_once_with(job_id)
    mock_repo.find_one.assert_called_once_with(mock_spec_class.return_value.by_id())
    assert original_job.state == State.NOT_STARTED
    assert original_job.start == "2023-10-09T12:00:01"
    assert original_job.status_message == "Job is running"
    assert original_job.input == {"output_key": "previous_output"}  # Ensure this remains unchanged
    assert original_job.stacktrace == "Some stacktrace info"
    mock_repo.update_one.assert_called_once_with(original_job)


def make_request(**kwargs) -> AutoreductionRequest:
    """
    Build a valid AutoreductionRequest.
    """
    return AutoreductionRequest(
        filename=kwargs.get("filename", "file.fits"),
        rb_number=kwargs.get("rb_number", "123"),
        instrument_name=kwargs.get("instrument_name", "CAM1"),
        title=kwargs.get("title", "My Run"),
        users=kwargs.get("users", "alice,bob"),
        run_start=kwargs.get("run_start", "2025-04-20T00:00:00"),
        run_end=kwargs.get("run_end", "2025-04-20T01:00:00"),
        good_frames=kwargs.get("good_frames", 10),
        raw_frames=kwargs.get("raw_frames", 20),
        additional_values=kwargs.get("additional_values", {"a": 1}),
        runner_image=kwargs.get("runner_image", "python:3.9"),
    )


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job._SCRIPT_REPO")
@patch("fia_api.core.services.job.hash_script")
@patch("fia_api.core.services.job.get_script_for_job")
@patch("fia_api.core.services.job._RUN_REPO")
def test_run_exists_creates_job_with_new_script(
    mock_run_repo,
    mock_get_script,
    mock_hash_script,
    mock_script_repo,
    mock_job_repo,
):
    existing_run = Mock(spec=Run)
    existing_run.id = 42
    existing_run.owner_id = 7
    existing_run.instrument_id = 99
    existing_run.instrument = Mock(spec=Instrument, instrument_name="CAM1")
    mock_run_repo.find_one.return_value = existing_run

    pre_script = Mock(value="print('do work')", sha="deadbeef")
    mock_get_script.return_value = pre_script
    mock_hash_script.return_value = "deadbeef"
    mock_script_repo.find_one.return_value = None

    req = make_request(
        filename="foo.fits",
        additional_values={"x": 1},
        runner_image="python:3.10",
        instrument_name="CAM1",
        rb_number="123",
    )

    returned_job = Mock()
    mock_job_repo.add_one.return_value = returned_job

    result = create_autoreduction_job(req)
    assert result is returned_job

    mock_run_repo.find_one.assert_called_once_with(ANY)  # we looked up by filename
    mock_get_script.assert_called_once_with("CAM1", ANY)
    mock_hash_script.assert_called_once_with(pre_script.value)

    passed_job = mock_job_repo.add_one.call_args[0][0]
    assert isinstance(passed_job.script, Script)
    assert passed_job.script.script == pre_script.value
    assert passed_job.script.sha == pre_script.sha
    assert passed_job.script_id is None

    assert passed_job.runner_image == "python:3.10"
    assert passed_job.job_type == JobType.AUTOREDUCTION
    assert passed_job.inputs == {"x": 1}
    assert passed_job.run_id == existing_run.id
    assert passed_job.owner_id == existing_run.owner_id
    assert passed_job.instrument_id == existing_run.instrument_id


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job._SCRIPT_REPO")
@patch("fia_api.core.services.job.hash_script")
@patch("fia_api.core.services.job.get_script_for_job")
@patch("fia_api.core.services.job._RUN_REPO")
def test_run_exists_reuses_existing_script(
    mock_run_repo,
    mock_get_script,
    mock_hash_script,
    mock_script_repo,
    mock_job_repo,
):
    existing_run = Mock(spec=Run)
    existing_run.id = 7
    existing_run.owner_id = 5
    existing_run.instrument_id = 11
    existing_run.instrument = Mock(spec=Instrument, instrument_name="CAM2")
    mock_run_repo.find_one.return_value = existing_run

    pre_script = Mock(value="do it", sha="cafebabe")
    mock_get_script.return_value = pre_script
    mock_hash_script.return_value = "cafebabe"

    existing_script = Mock(spec=Script, id=314)
    mock_script_repo.find_one.return_value = existing_script

    req = make_request(
        filename="bar.fits",
        additional_values={},
        runner_image="img:latest",
        instrument_name="CAM2",
        rb_number="999",
    )

    returned_job = Mock()
    mock_job_repo.add_one.return_value = returned_job

    result = create_autoreduction_job(req)
    assert result is returned_job

    passed_job = mock_job_repo.add_one.call_args[0][0]
    assert passed_job.script_id == existing_script.id
    assert not hasattr(passed_job, "script") or passed_job.script is None


@patch("fia_api.core.services.job._JOB_REPO")
@patch("fia_api.core.services.job._SCRIPT_REPO")
@patch("fia_api.core.services.job.hash_script")
@patch("fia_api.core.services.job.get_script_for_job")
@patch("fia_api.core.services.job._OWNER_REPO")
@patch("fia_api.core.services.job._INSTRUMENT_REPO")
@patch("fia_api.core.services.job._RUN_REPO")
def test_run_not_exists_creates_instrument_owner_run_and_new_script(
    mock_run_repo,
    mock_instrument_repo,
    mock_owner_repo,
    mock_get_script,
    mock_hash_script,
    mock_script_repo,
    mock_job_repo,
):
    mock_run_repo.find_one.return_value = None

    mock_instrument_repo.find_one.return_value = None
    new_instr = Mock(spec=Instrument, id=77, instrument_name="XYZ")
    mock_instrument_repo.add_one.return_value = new_instr

    mock_owner_repo.find_one.return_value = None
    new_owner = Mock(spec=JobOwner, id=88, experiment_number=4321)
    mock_owner_repo.add_one.return_value = new_owner

    created_run = Mock(spec=Run, id=99)
    mock_run_repo.add_one.return_value = created_run

    pre_script = Mock(value="xyz", sha="00ff")
    mock_get_script.return_value = pre_script
    mock_hash_script.return_value = "00ff"
    mock_script_repo.find_one.return_value = None

    req = make_request(
        filename="baz.fits",
        additional_values={"k": "v"},
        runner_image="ri",
        instrument_name="XYZ",
        rb_number="4321",
        good_frames=3,
        raw_frames=5,
    )

    returned_job = Mock()
    mock_job_repo.add_one.return_value = returned_job

    result = create_autoreduction_job(req)
    assert result is returned_job

    mock_instrument_repo.find_one.assert_called_once_with(ANY)
    inst_arg = mock_instrument_repo.add_one.call_args[0][0]
    assert isinstance(inst_arg, Instrument)
    assert inst_arg.instrument_name == "XYZ"

    mock_owner_repo.find_one.assert_called_once_with(ANY)
    owner_arg = mock_owner_repo.add_one.call_args[0][0]
    assert isinstance(owner_arg, JobOwner)
    assert owner_arg.experiment_number == 4321  # noqa: PLR2004

    run_arg = mock_run_repo.add_one.call_args[0][0]
    assert isinstance(run_arg, Run)
    assert run_arg.filename == "baz.fits"
    assert run_arg.owner_id == new_owner.id
    assert run_arg.instrument_id == new_instr.id
    assert run_arg.good_frames == 3  # noqa: PLR2004
    assert run_arg.raw_frames == 5  # noqa: PLR2004

    passed_job = mock_job_repo.add_one.call_args[0][0]
    assert isinstance(passed_job.script, Script)
    assert passed_job.script.sha == "00ff"
    assert passed_job.script.script == pre_script.value

    assert passed_job.run_id == created_run.id
    assert passed_job.owner_id == new_owner.id
    assert passed_job.instrument_id == new_instr.id
