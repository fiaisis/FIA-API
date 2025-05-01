"""Common transform for mantid scripts"""

import logging
import os

from fia_api.core.models import Job
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.transform import Transform

logger = logging.getLogger(__name__)


class MantidTransform(Transform):
    """Applies mantid common transform. Currently adding a github token"""

    def apply(self, script: PreScript, job: Job) -> None:
        logger.info("Applying mantid transform for job %s", job.id)
        lines = [line for line in script.value.splitlines() if not line.startswith("from __future")]
        future_import_lines = [line for line in script.value.splitlines() if line.startswith("from __future")]

        new_lines = [
            "from mantid.kernel import ConfigService",
            f'ConfigService.Instance()["network.github.api_token"] = "{os.getenv("GITHUB_API_TOKEN", "")}"',
        ]
        new_lines.extend(lines)
        future_import_lines.extend(new_lines)
        script.value = "\n".join(future_import_lines)
        logger.info("Transform complete for %s", job.id)
