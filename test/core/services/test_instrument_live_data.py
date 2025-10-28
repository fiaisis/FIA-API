from unittest.mock import Mock, patch

import pytest

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.services.instrument import (
    get_live_data_script_by_instrument_name,
    update_live_data_script_for_instrument,
)

