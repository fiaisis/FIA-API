import os

from github import Github

from fia_api.core.models import InstrumentString

TOKEN = os.environ.get("SCRIPT_WRITE_TOKEN", "shh")

GITHUB = Github(TOKEN)
script_repo = GITHUB.get_repo("fiaisis/autoreduction-scripts")


class LiveDataScript:
    def __init__(self, instrument: InstrumentString) -> None:
        self.instrument = instrument
        self.value, self._file_sha = self._fetch_latest_script()

    def _fetch_latest_script(self) -> tuple[str, str]:
        file = script_repo.get_contents(f"{self.instrument.upper()}/live_data.py")
        return file.decoded_content.decode(), file.sha

    def update(self, value: str) -> None:
        """
        Update the script in the remote repository
        :return: None
        """
        script_repo.update_file(
            f"{self.instrument.upper()}/live_data.py",
            f"FIA-API triggered {self.instrument} live data script update",
            value,
            self._file_sha,
        )
