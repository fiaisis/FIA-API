import os
from typing import cast

from github import Auth, Github, InputGitAuthor
from github.ContentFile import ContentFile

from fia_api.core.models import InstrumentString

TOKEN = os.environ.get("SCRIPT_WRITE_TOKEN", "shh")


class LiveDataScript:
    def __init__(self, instrument: InstrumentString) -> None:
        # We create the repo instance inside the init to prevent pygithub from attempting gh connection on import
        auth = Auth.Token(token=TOKEN)
        github = Github(auth=auth)
        self._script_repo = github.get_repo("fiaisis/autoreduction-scripts")

        self.instrument = instrument
        self.value, self._file_sha = self._fetch_latest_script()

    def _fetch_latest_script(self) -> tuple[str, str]:
        file = cast(
            ContentFile,  # noqa: TC006, remove at own peril
            self._script_repo.get_contents(f"{self.instrument.upper()}/live_data.py"),
        )  # safe cast as getting file not dir
        return file.decoded_content.decode(), file.sha

    def update(self, value: str) -> None:
        """
        Update the script in the remote repository
        :return: None
        """
        self._script_repo.update_file(
            f"{self.instrument.upper()}/live_data.py",
            f"FIA-API triggered {self.instrument} live data script update",
            value,
            self._file_sha,
            committer=InputGitAuthor("fiaisis", "fia@stfc.ac.uk"),
        )
