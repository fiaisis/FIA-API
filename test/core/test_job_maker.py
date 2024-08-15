import json
from unittest import mock

import pytest  # type: ignore

from fia_api.core.job_maker import JobMaker
from test.utils import FIA_FAKER_PROVIDER

faker = FIA_FAKER_PROVIDER


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
def test_rerun_job_experiment_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    job_id = faker.generator.random.randint(1, 10000)
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    experiment_number = faker.generator.random.randint(1, 1000000)

    job_maker.rerun_job(job_id=job_id, runner_image=runner_image, script=script, experiment_number=experiment_number)

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps(
            {"job_id": job_id, "runner_image": runner_image, "script": script, "experiment_number": experiment_number}
        )
    )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_rerun_job_user_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    job_id = faker.generator.random.randint(1, 10000)
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = faker.generator.random.randint(1, 1000000)

    job_maker.rerun_job(job_id=job_id, runner_image=runner_image, script=script, user_number=user_number)

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps({"job_id": job_id, "runner_image": runner_image, "script": script, "user_number": user_number})
    )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_rerun_job_user_and_experiment_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    job_id = faker.generator.random.randint(1, 10000)
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = faker.generator.random.randint(1, 1000000)
    experiment_number = faker.generator.random.randint(1, 1000000)

    job_maker.rerun_job(
        job_id=job_id,
        runner_image=runner_image,
        script=script,
        user_number=user_number,
        experiment_number=experiment_number,
    )

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps(
            {"job_id": job_id, "runner_image": runner_image, "script": script, "experiment_number": experiment_number}
        )
    )


def test_rerun_job_user_and_experiment_number_is_none():
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    job_id = faker.generator.random.randint(1, 10000)
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = None
    experiment_number = None

    with pytest.raises(ValueError):  # noqa: PT011
        job_maker.rerun_job(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
            user_number=user_number,
            experiment_number=experiment_number,
        )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_simple_job_experiment_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    experiment_number = faker.generator.random.randint(1, 1000000)

    job_maker.simple_job(runner_image=runner_image, script=script, experiment_number=experiment_number)

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps({"runner_image": runner_image, "script": script, "experiment_number": experiment_number})
    )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_simple_job_user_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = faker.generator.random.randint(1, 1000000)

    job_maker.simple_job(runner_image=runner_image, script=script, user_number=user_number)

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps({"runner_image": runner_image, "script": script, "user_number": user_number})
    )


@mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker")
def test_simple_job_user_and_experiment_number(broker):
    job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = faker.generator.random.randint(1, 1000000)
    experiment_number = faker.generator.random.randint(1, 1000000)

    job_maker.simple_job(
        runner_image=runner_image, script=script, user_number=user_number, experiment_number=experiment_number
    )

    assert broker.call_count == 1
    assert broker.call_arg == mock.call()
    assert job_maker._send_message.call_count == 1
    assert job_maker._send_message.call_args == mock.call(
        json.dumps({"runner_image": runner_image, "script": script, "experiment_number": experiment_number})
    )


def test_simple_job_user_and_experiment_number_is_none():
    with mock.patch("fia_api.core.job_maker.JobMaker._connect_to_broker"):
        job_maker = JobMaker("", "", "", "")
    job_maker._send_message = mock.MagicMock()
    runner_image = str(mock.MagicMock())
    script = str(mock.MagicMock())
    user_number = None
    experiment_number = None

    with pytest.raises(ValueError):  # noqa: PT011
        job_maker.simple_job(
            runner_image=runner_image, script=script, user_number=user_number, experiment_number=experiment_number
        )
