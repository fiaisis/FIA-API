"""Test cases for MariTransform"""

from unittest.mock import Mock

import pytest

from fia_api.scripts.pre_script import PreScript
from fia_api.scripts.transforms.mari_transforms import MariTransform


@pytest.fixture
def script():
    """
    MariTransform  PreScript fixture
    :return:
    """
    return PreScript(
        value="""from __future__ import print_function

import requests as requests

with open("MARIReduction_Sample.py", "w+") as fle:
    text = requests.get("https://raw.githubusercontent.com/mantidproject/scriptrepository/master/direct_inelastic/MARI/MARIReduction_Sample.py").text
    fle.write(text)

with open("mask_file.xml", "w+" as fle):
    text = requests.get("url_to_mask_file.xml").text
    fle.write(text)

with open("mari_res2013.map", "w+" as fle):
    text = requests.get("https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_res2013.map").text
    fle.write(text)


from mantid import config
from MARIReduction_Sample import *
import time
import os
import datetime
import sys
if sys.version_info > (3,):
    if sys.version_info < (3,4):
        from imp import reload
    else:
        from importlib import reload
try:
    #Note: due to the mantid-python implementation, one needs to run this
    #script in Mantid  script window  TWICE!!!  to deploy the the changes made to MARIReduction_Sample.py file.
    sys.path.insert(0,'/output')
    reload(sys.modules['MARIReduction_Sample'])
except:
    print("*** WARNING can not reload MARIReduction_Sample file")
    pass

# Run number and Ei
runno=26644
sum_runs=False
ei=[30, 11.8]

# White vanadium run number
wbvan=28580

# Default save directory (/output only for autoreduction as the RBNumber/autoreduced dir is mounted here)
config['defaultsave.directory'] = '/output' #data_dir

# Absolute normalisation parameters
#monovan=21803
#sam_mass=41.104
#sam_rmm=398.9439
monovan=0
sam_mass=0
sam_rmm=0

# Set to true to remove the constant ToF background from the data.
remove_bkg = True

# If necessary, add any sequence of reduction paramerters defined in MARIParameters.xml file
# to the end ot the illiad string using the form: property=value
# (e.g.:  iliad_mari(runno,ei,wbvan,monovan,sam_mass,sam_rmm,sum_runs,check_background=False)
output_ws = iliad_mari(runno, ei, wbvan, monovan, sam_mass, sam_rmm, sum_runs, check_background=remove_bkg, hard_mask_file='mask_file.xml')

# To run reduction _and_ compute density of states together uncomment this and comment iliad_mari above
# bkgruns and runno can be lists, which means those runs will be summed, and the sum is reduced
#bkgruns = 20941
#iliad_dos(runno, wbvan, ei, monovan, sam_mass, sam_rmm, sum_runs, background=bkgrun, temperature=5)

# Output set for autoreduction
output = [f'/output/{output_ws.getName()}.nxs']"""
    )


@pytest.fixture
def reduction():
    """
    Reduction fixture
    :return:
    """
    mock = Mock()
    mock.inputs = {
        "runno": 12345,
        "sum_runs": True,
        "ei": [50, 20],
        "monovan": 54321,
        "sam_mass": 30,
        "sam_rmm": 400,
        "remove_bkg": False,
        "mask_file_link": "Some link",
        "wbvan": 12345,
    }
    return mock


def test_mari_transform_apply(script, reduction):  # noqa: C901
    """
    Test mari transform applies correct updates to script
    :param script: The script fixture
    :param reduction: The reduction fixture
    :return: None
    """
    transform = MariTransform()

    original_lines = script.value.splitlines()
    transform.apply(script, reduction)
    updated_lines = script.value.splitlines()
    assert len(original_lines) == len(updated_lines)
    url_replaced = False
    for index, line in enumerate(updated_lines):
        if '    text = requests.get("Some link").text' in line:
            url_replaced = True
            continue
        if line.startswith("runno"):
            assert line == "runno = 12345"
        elif line.startswith("sum_runs"):
            assert line == "sum_runs = True"
        elif line.startswith("ei"):
            assert line == "ei = [50, 20]"
        elif line.startswith("wbvan"):
            assert line == "wbvan = 12345"
        elif line.startswith("monovan"):
            assert line == "monovan = 54321"
        elif line.startswith("sam_mass"):
            assert line == "sam_mass = 30"
        elif line.startswith("sam_rmm"):
            assert line == "sam_rmm = 400"
        elif line.startswith("remove_bkg"):
            assert line == "remove_bkg = False"
        else:
            assert line == original_lines[index]
    assert url_replaced
