"""Tests for output_transforms.py"""

from unittest.mock import Mock
from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.output_transform import OutputTransform

SCRIPT = """# import os
print(hello, world)
"""

def test_output_transform():
  """
  """
  script_addon = (
            "import json\n"
            "\n"
            "print(json.dumps({'status': 'Successful', 'status_message':"
            "'','output_files': output, 'stacktrace': ''}))\n"
        )
  script = PreScript(value=SCRIPT)
  OutputTransform().apply(script, Mock())

  assert script.value.endswith(script_addon)
