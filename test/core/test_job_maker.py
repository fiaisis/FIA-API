import json
from pathlib import Path
from unittest import mock

import pytest  # type: ignore

from fia_api.core.exceptions import JobRequestError
from fia_api.core.job_maker import JobMaker


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_send_message(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker.channel = mock.MagicMock()
    custom_message = str(mock.MagicMock())

    job_maker._send_message(custom_message)

    assert broker.call_count == 2  # noqa: PLR2004
    assert broker.call_args == [mock.call(), mock.call()]
    assert job_maker.channel.basic_publish.call_count == 1
    assert job_maker.channel.basic_publish.call_args == mock.call(exchange="", routing_key="", body=custom_message)


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_rerun_job_no_run(mock_connect, faker):
    job_maker = JobMaker("", "", "", "test_queue")
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
    job_maker = JobMaker("", "", "", "test_queue")
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
    }
    sent_message = job_maker._send_message.call_args[0][0]
    assert json.loads(sent_message) == expected_dict


def test_create_rerun_job_require_owner(faker):
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "test_queue")
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
    job_maker = JobMaker("", "", "", "test_queue")
    job_maker._send_message = mock.MagicMock()
    job_maker._job_repo.find_one = mock.MagicMock(return_value=None)

    job_id = faker.random.randint(1, 10000)
    runner_image = "runner_img"
    script = "print('not found')"
    experiment_number = faker.random.randint(1, 1000000)

    with pytest.raises(JobRequestError, match="Cannot rerun job that does not exist."):
        job_maker.create_rerun_job(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
            experiment_number=experiment_number,
        )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_create_simple_job_success(mock_connect, faker):
    job_maker = JobMaker("", "", "", "test_queue")
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
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "test_queue")
    job_maker._send_message = mock.MagicMock()
    runner_image = "simple_runner"
    script = "print('error')"
    with pytest.raises(JobRequestError):
        job_maker.create_simple_job(runner_image=runner_image, script=script, user_number=None, experiment_number=None)
