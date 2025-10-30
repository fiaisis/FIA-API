"""
Module containing test constants.
"""
import datetime

from fia_api.core.models import JobOwner, Instrument, Script, Job, State, JobType, Run

USER_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # noqa: S105
    ".eyJ1c2VybnVtYmVyIjoxMjM0LCJyb2xlIjoidXNlciIsInVzZXJuYW1lIjoiZm9vIiwiZXhwIjo0ODcyNDY4MjYzfQ."
    "99rVB56Y6-_rJikqlZQia6koEJJcpY0T_QV-fZ43Mok"
)
STAFF_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."  # noqa: S105
    "eyJ1c2VybnVtYmVyIjoxMjM0LCJyb2xlIjoic3RhZmYiLCJ1c2VybmFtZSI6ImZvbyIsImV4cCI6NDg3MjQ2ODk4M30."
    "-ktYEwdUfg5_PmUocmrAonZ6lwPJdcMoklWnVME1wLE"
)

STAFF_HEADER = {"Authorization": f"Bearer {STAFF_TOKEN}"}
USER_HEADER = {"Authorization": f"Bearer {USER_TOKEN}"}
API_KEY_HEADER = {"Authorization": "Bearer shh"}
TEST_JOB_OWNER = JobOwner(experiment_number=18204970)
TEST_INSTRUMENT = Instrument(instrument_name="NEWBIE", latest_run=1, specification={"foo": "bar"})
TEST_SCRIPT = Script(script="print('Script 1')", sha="some_sha", script_hash="some_hash")
TEST_JOB = Job(
    start=datetime.datetime.now(datetime.UTC),
    owner=TEST_JOB_OWNER,
    state=State.NOT_STARTED,
    inputs={"input": "value"},
    script=TEST_SCRIPT,
    instrument=TEST_INSTRUMENT,
    job_type=JobType.AUTOREDUCTION,
)
TEST_RUN = Run(
    filename="test_run",
    owner=TEST_JOB_OWNER,
    title="Test Run",
    users="User1, User2",
    run_start=datetime.datetime.now(datetime.UTC),
    run_end=datetime.datetime.now(datetime.UTC),
    good_frames=200,
    raw_frames=200,
    instrument=TEST_INSTRUMENT,
)
