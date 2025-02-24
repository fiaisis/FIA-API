"""Testing utils"""

import random
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from db.data_models import Base, Instrument, Job, JobOwner, JobType, Run, Script, State
from faker import Faker
from faker.providers import BaseProvider

from fia_api.core.repositories import ENGINE, SESSION


class FIAProvider(BaseProvider):
    """Custom fia faker provider"""

    INSTRUMENTS: ClassVar[list[str]] = [
        "ALF",
        "ARGUS",
        "CHIPIR",
        "CHRONUS",
        "CRISP",
        "EMU",
        "ENGINX",
        "GEM",
        "HET",
        "HIFI",
        "HRPD",
        "IMAT",
        "INES",
        "INTER",
        "IRIS",
        "LARMOR",
        "LET",
        "LOQ",
        "MAPS",
        "MARI",
        "MERLIN",
        "MUSR",
        "NILE",
        "NIMROD",
        "OFFSPEC",
        "OSIRIS",
        "PEARL",
        "POLARIS",
        "POLREF",
        "SANDALS",
        "SANS2D",
        "SURF",
        "SXD",
        "TOSCA",
        "VESUVIO",
        "WISH",
        "ZOOM",
    ]

    @staticmethod
    def start_time(faker: Faker) -> datetime:
        """
        Generate a start time
        :return:
        """
        return datetime(
            faker.pyint(min_value=2017, max_value=2023),
            faker.pyint(min_value=1, max_value=12),
            faker.pyint(min_value=1, max_value=28),
            faker.pyint(min_value=0, max_value=23),
            faker.pyint(min_value=0, max_value=59),
            faker.pyint(min_value=0, max_value=59),
            tzinfo=UTC,
        )

    def instrument(self, faker: Faker) -> Instrument:
        """
        Generate a random instrument from the list
        :return:
        """
        instrument = Instrument()
        instrument.instrument_name = random.choice(self.INSTRUMENTS)  # noqa: S311
        instrument.specification = faker.pydict(
            nb_elements=faker.pyint(min_value=1, max_value=10), value_types=[str, int, bool, float]
        )
        return instrument

    def run(self, instrument: Instrument, faker: Faker) -> Run:
        """
        Given an instrument generate a random run model
        :param instrument: The Instrument
        :param faker: Faker provider to use
        :return: random run model
        """
        run = Run()
        run_start = self.start_time(faker)
        run_end = run_start + timedelta(minutes=faker.pyint(max_value=50))
        experiment_number = faker.unique.pyint(min_value=10000, max_value=999999)
        raw_frames = faker.pyint(min_value=1000)
        good_frames = faker.pyint(max_value=raw_frames)
        title = faker.unique.sentence(nb_words=10)
        run.filename = (
            f"/archive/NDX{instrument.instrument_name}/Instrument/data/"
            f"cycle_{faker.pyint(min_value=15, max_value=23)}_0{faker.pyint(min_value=1, max_value=3)}/"
            f"{instrument.instrument_name}{experiment_number}.nxs"
        )
        run.title = title
        run.instrument = instrument
        run.raw_frames = raw_frames
        run.good_frames = good_frames
        run.users = f"{faker.first_name()} {faker.last_name()}, {faker.first_name()} {faker.last_name()}"
        run.run_start = run_start
        run.run_end = run_end
        run.owner = JobOwner(experiment_number=experiment_number)

        return run

    def job(self, instrument: Instrument, faker: Faker) -> Job:
        """
        Generate a random job Model
        :return: The job model
        """
        job = Job()
        state = faker.enum(State)
        if state != State.NOT_STARTED:
            job.start = self.start_time(faker)
            job.end = job.start + timedelta(minutes=faker.pyint(max_value=50))
            job.status_message = faker.sentence(nb_words=10)
            job.outputs = "What should this be?"
        job.inputs = faker.pydict(
            nb_elements=faker.pyint(min_value=1, max_value=10),
            value_types=[str, int, bool, float],
        )
        job.state = state
        job.stacktrace = "some stacktrace"
        job.owner = JobOwner(experiment_number=faker.unique.pyint(min_value=10000, max_value=999999))
        job.instrument = instrument
        job.job_type = faker.enum(JobType)
        return job

    def script(self, faker: Faker) -> Script:
        """
        Generate a random script model
        :return: The script model
        """
        script = Script()
        script.sha = faker.unique.sha1()
        script.script_hash = "some_hash"
        script.script = "import os\nprint('foo')\n"
        return script

    def insertable_job(self, instrument: Instrument, faker: Faker) -> Job:
        """
        Given an instrument model, generate random; job, run, and script all related.
        :param instrument:The instrument
        :return: The job with relations
        """
        job = self.job(instrument, faker)
        job.run = self.run(instrument, faker)
        job.script = self.script(faker)

        return job


TEST_INSTRUMENT = Instrument(instrument_name="TEST", specification={})
TEST_JOB_OWNER = JobOwner(experiment_number=1820497)
TEST_JOB = Job(
    inputs={
        "ei": "'auto'",
        "sam_mass": 0.0,
        "sam_rmm": 0.0,
        "monovan": 0,
        "remove_bkg": True,
        "sum_runs": False,
        "runno": 25581,
        "mask_file_link": "https://raw.githubusercontent.com/pace-neutrons/InstrumentFiles/"
        "964733aec28b00b13f32fb61afa363a74dd62130/mari/mari_mask2023_1.xml",
        "wbvan": 12345,
    },
    state=State.NOT_STARTED,
    owner=TEST_JOB_OWNER,
    instrument=TEST_INSTRUMENT,
    job_type=JobType.AUTOREDUCTION,
)
TEST_RUN = Run(
    instrument=TEST_INSTRUMENT,
    title="Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
    owner=TEST_JOB_OWNER,
    filename="MAR25581.nxs",
    run_start="2019-03-22T10:15:44",
    run_end="2019-03-22T10:18:26",
    raw_frames=8067,
    good_frames=6452,
    users="Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
    jobs=[TEST_JOB],
)


def setup_database(faker: Faker) -> None:
    """Set up database for e2e tests"""
    fia_faker = FIAProvider(faker)
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    with SESSION() as session:
        instruments = []
        for instrument in fia_faker.INSTRUMENTS:
            instrument_ = Instrument()
            instrument_.instrument_name = instrument
            instrument_.specification = fia_faker.instrument(faker).specification
            instruments.append(instrument_)
        for _ in range(5000):
            session.add(fia_faker.insertable_job(random.choice(instruments), faker))  # noqa: S311
        session.add(TEST_JOB)
        session.commit()
        session.refresh(TEST_JOB)
