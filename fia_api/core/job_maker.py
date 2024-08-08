import json


class JobMaker:
    def __init__(self):
        # Connect to Rabbit
        pass

    def _send_message(self, message: str) -> None:
        pass

    def rerun_job(
        self,
        job_id: int,
        runner_image: str,
        script: str,
        experiment_number: int | None = None,
        user_number: int | None = None,
    ) -> None:
        """
        Default to using experiment_number over user_number
        :param job_id:
        :param runner_image:
        :param script:
        :param experiment_number:
        :param user_number:
        :return: None
        """
        json_dict = {"job_id": job_id, "runner_image": runner_image, "script": script}
        if experiment_number is not None:
            json_dict["experiment_number"] = experiment_number
        elif user_number is not None:
            json_dict["user_number"] = user_number
        else:
            raise ValueError("Something needs to own the job, either experiment_number or user_number.")
        self._send_message(json.dumps(json_dict))

    def simple_job(
        self, runner_image: str, script: str, experiment_number: int | None = None, user_number: int | None = None
    ) -> None:
        """
        Default to using experiment_number over user_number
        :param runner_image:
        :param script:
        :param experiment_number:
        :param user_number:
        :return: None
        """
        json_dict = {"runner_image": runner_image, "script": script}
        if experiment_number is not None:
            json_dict["experiment_number"] = experiment_number
        elif user_number is not None:
            json_dict["user_number"] = user_number
        else:
            raise ValueError("Something needs to own the job, either experiment_number or user_number.")
        self._send_message(json.dumps(json_dict))
