"""
Testing utils
"""

import random
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from faker import Faker
from faker.providers import BaseProvider

from fia_api.core.model import Base, Instrument, Reduction, ReductionState, Run, Script
from fia_api.core.repositories import ENGINE, SESSION

random.seed(1)
Faker.seed(1)
faker = Faker()


class FIAProvider(BaseProvider):
    """
    Custom fia faker provider
    """

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
    def start_time() -> datetime:
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

    def instrument(self) -> Instrument:
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

    def run(self, instrument: Instrument) -> Run:
        """
        Given an instrument generate a random run model
        :param instrument: The Instrument
        :return: random run model
        """
        run = Run()
        run_start = self.start_time()
        run_end = run_start + timedelta(minutes=faker.pyint(max_value=50))
        experiment_number = faker.unique.pyint(min_value=10000, max_value=99999)
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
        run.experiment_number = experiment_number
        run.run_start = run_start
        run.run_end = run_end

        return run

    def reduction(self) -> Reduction:
        """
        Generate a random Reduction Model
        :return: The reduction model
        """
        reduction = Reduction()
        reduction_state = faker.enum(ReductionState)
        if reduction_state != ReductionState.NOT_STARTED:
            reduction.reduction_start = self.start_time()
            reduction.reduction_end = reduction.reduction_start + timedelta(minutes=faker.pyint(max_value=50))
            reduction.reduction_status_message = faker.sentence(nb_words=10)
            reduction.reduction_outputs = "What should this be?"
        reduction.reduction_inputs = faker.pydict(
            nb_elements=faker.pyint(min_value=1, max_value=10),
            value_types=[str, int, bool, float],
        )
        reduction.reduction_state = reduction_state
        reduction.stacktrace = "some stacktrace"
        return reduction

    def script(self) -> Script:
        """
        Generate a random script model
        :return: The script model
        """
        script = Script()
        script.sha = faker.unique.sha1()
        script.script_hash = "some_hash"
        script.script = "import os\nprint('foo')\n"
        return script

    def insertable_reduction(self, instrument: Instrument) -> Reduction:
        """
        Given an instrument model, generate random; reduction, run, and script all related.
        :param instrument:The instrument
        :return: The reduction with relations
        """
        reduction = self.reduction()
        reduction.runs = [self.run(instrument)]
        reduction.script = self.script()

        return reduction


FIA_FAKER_PROVIDER = FIAProvider(faker)

TEST_INSTRUMENT = Instrument(instrument_name="TEST", specification={})
TEST_REDUCTION = Reduction(
    reduction_inputs={
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
    reduction_state=ReductionState.NOT_STARTED,
)
TEST_RUN = Run(
    instrument=TEST_INSTRUMENT,
    title="Whitebeam - vanadium - detector tests - vacuum bad - HT on not on all LAB",
    experiment_number=1820497,
    filename="MAR25581.nxs",
    run_start="2019-03-22T10:15:44",
    run_end="2019-03-22T10:18:26",
    raw_frames=8067,
    good_frames=6452,
    users="Wood,Guidi,Benedek,Mansson,Juranyi,Nocerino,Forslund,Matsubara",
    reductions=[TEST_REDUCTION],
)


def setup_database() -> None:
    """Setup database for e2e tests"""
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    with SESSION() as session:
        instruments = []
        for instrument in FIA_FAKER_PROVIDER.INSTRUMENTS:
            instrument_ = Instrument()
            instrument_.instrument_name = instrument
            instrument_.specification = FIA_FAKER_PROVIDER.instrument().specification
            instruments.append(instrument_)
        for _ in range(5000):
            session.add(FIA_FAKER_PROVIDER.insertable_reduction(random.choice(instruments)))  # noqa: S311
        session.add(TEST_REDUCTION)
        session.commit()
        session.refresh(TEST_REDUCTION)
