from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform


class OutputTransform(Transform):
    def apply(self, script: PreScript, _: Job) -> None:
        """
        The aim is to force whatever the script that is passed to also output to stdinput a json string that consists of
        3 values, status of the run (status), status message, and output files.
        :return: The passed script with 3 lines added to ensure a json dump occurs at the end
        """
        script_addon = (
            "import json\n"
            "\n"
            "print(json.dumps({'status': 'Successful', 'status_message':"
            "'','output_files': output, 'stacktrace': ''}))\n"
        )
        script.value = script.value + "\n" + script_addon
