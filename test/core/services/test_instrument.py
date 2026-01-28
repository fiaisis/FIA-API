from unittest.mock import Mock, patch

import pytest

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.services.instrument import (
    get_instruments_with_live_data_support,
    get_latest_run_by_instrument_name,
    get_live_data_script_by_instrument_name,
    get_specification_by_instrument_name,
    update_latest_run_for_instrument,
    update_live_data_script_for_instrument,
    update_specification_for_instrument,
)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_specification_by_instrument_name(mock_spec, mock_repo):
    mock_instrument = Mock()
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.find_one.return_value = mock_instrument

    mock_spec_instance = Mock()
    mock_spec.return_value = mock_spec_instance
    mock_spec_instance.by_name.return_value = mock_instrument.specification

    spec = get_specification_by_instrument_name("mari", mock_session)

    assert spec == mock_instrument.specification
    mock_repo.assert_called_once_with(mock_session)
    mock_repo_instance.find_one.assert_called_once()
    mock_spec_instance.by_name.assert_called_once_with("mari")


@patch("fia_api.core.services.instrument.Repo")
def test_get_specification_by_instrument_name_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.find_one.return_value = None
    with patch("fia_api.core.services.instrument.InstrumentSpecification"), pytest.raises(MissingRecordError):
        get_specification_by_instrument_name(instrument_name="mari", session=mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_update_specification_for_instrument(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    instrument = Mock()

    mock_repo_instance.find_one.return_value = instrument

    update_specification_for_instrument("mari", {"foo": 1}, mock_session)

    mock_repo_instance.find_one.assert_called_once_with(mock_spec.return_value.by_name.return_value)
    assert instrument.specification == {"foo": 1}
    mock_repo_instance.update_one.assert_called_once_with(instrument)


@patch("fia_api.core.services.instrument.Repo")
def test_update_specification_for_instrument_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo_instance.find_one.return_value = None
        with pytest.raises(MissingRecordError):
            update_specification_for_instrument("mari", {"foo": 1}, mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_latest_run_by_instrument_name(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_instrument = Mock()
    mock_repo_instance.find_one.return_value = mock_instrument

    latest_run = get_latest_run_by_instrument_name("mari", mock_session)

    assert latest_run == mock_instrument.latest_run
    mock_spec.return_value.by_name.assert_called_once_with("mari")


@patch("fia_api.core.services.instrument.Repo")
def test_get_latest_run_by_instrument_name_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo_instance.find_one.return_value = None

        with pytest.raises(MissingRecordError):
            get_latest_run_by_instrument_name("mari", mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_update_latest_run_for_instrument(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    instrument = Mock()

    mock_repo_instance.find_one.return_value = instrument

    update_latest_run_for_instrument("mari", "MARI12345", mock_session)

    mock_repo_instance.find_one.assert_called_once_with(mock_spec.return_value.by_name.return_value)
    assert instrument.latest_run == "MARI12345"
    mock_repo_instance.update_one.assert_called_once_with(instrument)


@patch("fia_api.core.services.instrument.Repo")
def test_update_latest_run_for_instrument_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo_instance.find_one.return_value = None
        with pytest.raises(MissingRecordError):
            update_latest_run_for_instrument("mari", "MARI12345", mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_live_data_script_by_instrument_name(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_instrument = Mock()
    mock_instrument.live_data_script = "print('hello')"
    mock_repo_instance.find_one.return_value = mock_instrument

    script = get_live_data_script_by_instrument_name("mari", mock_session)

    assert script == mock_instrument.live_data_script
    mock_spec.return_value.by_name.assert_called_once_with("mari")


@patch("fia_api.core.services.instrument.Repo")
def test_get_live_data_script_by_instrument_name_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo_instance.find_one.return_value = None

        with pytest.raises(MissingRecordError):
            get_live_data_script_by_instrument_name("mari", mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_update_live_data_script_for_instrument(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    instrument = Mock()

    mock_repo_instance.find_one.return_value = instrument

    update_live_data_script_for_instrument("mari", "print('hello world')", mock_session)

    mock_repo_instance.find_one.assert_called_once_with(mock_spec.return_value.by_name.return_value)
    assert instrument.live_data_script == "print('hello world')"
    mock_repo_instance.update_one.assert_called_once_with(instrument)


@patch("fia_api.core.services.instrument.Repo")
def test_update_live_data_script_for_instrument_instrument_missing(mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo_instance.find_one.return_value = None
        with pytest.raises(MissingRecordError):
            update_live_data_script_for_instrument("mari", "print('hello world')", mock_session)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_instruments_with_live_data_support(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance

    mock_instrument_1 = Mock()
    mock_instrument_1.instrument_name = "mari"
    mock_instrument_2 = Mock()
    mock_instrument_2.instrument_name = "wish"
    mock_repo_instance.find.return_value = [mock_instrument_1, mock_instrument_2]

    instruments = get_instruments_with_live_data_support(mock_session)

    assert instruments == ["mari", "wish"]
    mock_repo.assert_called_once_with(mock_session)
    mock_spec.return_value.with_live_data_support.assert_called_once()
    mock_repo_instance.find.assert_called_once_with(mock_spec.return_value.with_live_data_support.return_value)


@patch("fia_api.core.services.instrument.Repo")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_instruments_with_live_data_support_returns_empty_list_when_none_found(mock_spec, mock_repo):
    mock_session = Mock()
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.find.return_value = []

    instruments = get_instruments_with_live_data_support(mock_session)

    assert instruments == []
    mock_repo.assert_called_once_with(mock_session)
    mock_spec.return_value.with_live_data_support.assert_called_once()
