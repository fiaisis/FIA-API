import json
from pathlib import Path
from unittest import mock

import pytest  # type: ignore
from requests.exceptions import RequestException

from fia_api.core.exceptions import JobRequestError, LLSPSubmissionFailureError
from fia_api.core.job_maker import JobMaker

NGEM_SCRIPT = """ngem = True
recon = False
ngem_path = "/ngem/nGEM-INES/DATA/IMAT_2026_01/IMAT00012345"
"""

RECON_SCRIPT = """ngem = False
recon = True
dataset_path = "/imat/RB123456/Tomo"
"""


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_send_message(broker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "", mock_session)
    job_maker.channel = mock.MagicMock()
    custom_message = str(mock.MagicMock())

    job_maker._send_message(custom_message)

    assert broker.call_count == 1
    assert broker.call_args == [mock.call(), mock.call()]
    assert job_maker.channel.basic_publish.call_count == 1
    assert job_maker.channel.basic_publish.call_args == mock.call(exchange="", routing_key="", body=custom_message)


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_rerun_job_no_run(mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    original_job = mock.MagicMock()
    original_job.run = None
    job_maker._job_repo.find_one = mock.MagicMock(return_value=original_job)
    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)
    rerun_job = mock.MagicMock()
    rerun_job.id = faker.random.randint(1000, 2000)
    rerun_job.run = None
    job_maker._job_repo.add_one = mock.MagicMock(return_value=rerun_job)

    job_id = faker.random.randint(1, 10000)
    runner_image = "runner_img"
    script = "print('hello')"
    experiment_number = faker.random.randint(1, 1000000)

    with pytest.raises(JobRequestError):
        job_maker.create_rerun_job(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
            experiment_number=experiment_number,
        )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_rerun_job_with_run(mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    dummy_run = mock.MagicMock()
    dummy_run.filename = "run_file.txt"
    dummy_run.instrument.instrument_name = "inst1"
    dummy_owner = mock.MagicMock()
    dummy_owner.experiment_number = faker.random.randint(1, 1000000)
    dummy_run.owner = dummy_owner

    original_job = mock.MagicMock()
    original_job.run = dummy_run
    job_maker._job_repo.find_one = mock.MagicMock(return_value=original_job)

    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)

    rerun_job = mock.MagicMock()
    rerun_job.id = faker.random.randint(1000, 2000)
    rerun_job.run = dummy_run
    job_maker._job_repo.add_one = mock.MagicMock(return_value=rerun_job)

    job_id = faker.random.randint(1, 10000)
    runner_image = "runner_img_run"
    script = "print('world')"
    experiment_number = faker.random.randint(1, 1000000)

    job_maker.create_rerun_job(
        job_id=job_id,
        runner_image=runner_image,
        script=script,
        experiment_number=experiment_number,
    )

    expected_dict = {
        "filename": Path(dummy_run.filename).stem,
        "instrument": dummy_run.instrument.instrument_name,
        "rb_number": dummy_run.owner.experiment_number,
        "job_id": rerun_job.id,
        "runner_image": runner_image,
        "script": script,
        "job_type": "rerun",
        "additional_values": {},
    }
    sent_message = job_maker._send_message.call_args[0][0]
    assert json.loads(sent_message) == expected_dict


def _rerun_job_maker_with_instrument(faker, instrument_name):
    """
    Build a job maker whose reruns always belong to the given instrument.
    :param faker: The faker fixture, for the ids.
    :param instrument_name: The instrument of the run being rerun.
    :return: The job maker, with the message sender and repositories mocked out.
    """
    job_maker = JobMaker("", "", "", "test_queue", mock.Mock())
    job_maker._send_message = mock.MagicMock()

    dummy_run = mock.MagicMock()
    dummy_run.filename = "run_file.nxs"
    dummy_run.instrument.instrument_name = instrument_name
    dummy_run.owner.experiment_number = faker.random.randint(1, 1000000)

    original_job = mock.MagicMock()
    original_job.run = dummy_run
    job_maker._job_repo.find_one = mock.MagicMock(return_value=original_job)
    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)

    rerun_job = mock.MagicMock()
    rerun_job.id = faker.random.randint(1000, 2000)
    rerun_job.run = dummy_run
    job_maker._job_repo.add_one = mock.MagicMock(return_value=rerun_job)
    return job_maker


@pytest.mark.parametrize(
    ("instrument_name", "script", "expected_inputs"),
    [
        ("IMAT", NGEM_SCRIPT, {"ngem": "true", "recon": "false"}),
        ("IMAT", RECON_SCRIPT, {}),
        ("IRIS", NGEM_SCRIPT, {}),
    ],
)
@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_rerun_job_recovers_ngem_from_script(mock_connect, faker, instrument_name, script, expected_inputs):
    job_maker = _rerun_job_maker_with_instrument(faker, instrument_name)

    job_maker.create_rerun_job(
        job_id=faker.random.randint(1, 10000),
        runner_image="runner_img",
        script=script,
        experiment_number=faker.random.randint(1, 1000000),
    )

    created_job = job_maker._job_repo.add_one.call_args[0][0]
    assert created_job.inputs == expected_inputs
    sent_message = json.loads(job_maker._send_message.call_args[0][0])
    assert sent_message["additional_values"] == expected_inputs


def test_create_rerun_job_require_owner(faker):
    mock_session = mock.Mock()
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    job_id = faker.random.randint(1, 10000)
    runner_image = "runner_img"
    script = "print('hello')"
    with pytest.raises(JobRequestError):
        job_maker.create_rerun_job(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
            user_number=None,
            experiment_number=None,
        )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_rerun_job_original_job_not_found(mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    job_maker._job_repo.find_one = mock.MagicMock(return_value=None)

    job_id = faker.random.randint(1, 10000)
    runner_image = "runner_img"
    script = "print('not found')"
    experiment_number = faker.random.randint(1, 1000000)

    with pytest.raises(JobRequestError, match=r"Cannot rerun job that does not exist."):
        job_maker.create_rerun_job(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
            experiment_number=experiment_number,
        )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_simple_job_success(mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)
    simple_job = mock.MagicMock()
    simple_job.id = faker.random.randint(1000, 2000)
    job_maker._job_repo.add_one = mock.MagicMock(return_value=simple_job)

    runner_image = "simple_runner"
    script = "print('simple')"
    experiment_number = faker.random.randint(1, 1000000)
    user_number = faker.random.randint(1, 1000000)

    job_maker.create_simple_job(
        runner_image=runner_image,
        script=script,
        experiment_number=experiment_number,
        user_number=user_number,
    )

    expected_dict = {
        "runner_image": runner_image,
        "script": script,
        "experiment_number": experiment_number,
        "user_number": user_number,
        "job_id": simple_job.id,
        "job_type": "simple",
    }
    sent_message = job_maker._send_message.call_args[0][0]
    assert json.loads(sent_message) == expected_dict


def test_create_simple_job_require_owner():
    mock_session = mock.Mock()
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._send_message = mock.MagicMock()
    runner_image = "simple_runner"
    script = "print('error')"
    with pytest.raises(JobRequestError):
        job_maker.create_simple_job(runner_image=runner_image, script=script, user_number=None, experiment_number=None)


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
@mock.patch("fia_api.core.job_maker.requests.post")
def test_create_fast_start_job_success(mock_post, mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)
    job = mock.MagicMock()
    job.id = faker.random.randint(1000, 2000)
    job_maker._job_repo.add_one = mock.MagicMock(return_value=job)

    runner_image = "fast_runner"
    script = "print('fast')"
    user_number = 12345

    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    job_id = job_maker.create_fast_start_job(runner_image=runner_image, script=script, user_number=user_number)

    assert job_id == job.id
    added_job = job_maker._job_repo.add_one.call_args[0][0]
    assert added_job.script is not None
    assert added_job.script.script == script
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"] == {"script": script, "job_id": job.id}
    # Check default header key 'shh'
    assert kwargs["headers"]["Authorization"] == "Bearer shh"


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
@mock.patch("fia_api.core.job_maker.requests.post")
def test_create_fast_start_job_failure(mock_post, mock_connect, faker):
    mock_session = mock.Mock()
    job_maker = JobMaker("", "", "", "test_queue", mock_session)
    # job setup ...
    job = mock.MagicMock()
    job.id = 1
    job_maker._job_repo.add_one = mock.MagicMock(return_value=job)
    job_maker._owner_repo.find_one = mock.MagicMock(return_value=None)
    job_maker._script_repo.find_one = mock.MagicMock(return_value=None)

    mock_post.side_effect = RequestException("Connection error")

    with pytest.raises(LLSPSubmissionFailureError, match="Failed to submit fast start job"):
        job_maker.create_fast_start_job(runner_image="img", script="print('fail')", user_number=123)
