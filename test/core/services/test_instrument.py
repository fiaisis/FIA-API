from unittest.mock import Mock, patch

import pytest

from fia_api.core.exceptions import MissingRecordError
from fia_api.core.services.instrument import get_specification_by_instrument_name, update_specification_for_instrument


@patch("fia_api.core.services.instrument._REPO")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_get_specification_by_instrument_name(mock_spec, mock_repo):
    mock_instrument = Mock()
    mock_repo.find_one.return_value = mock_instrument

    spec = get_specification_by_instrument_name("mari")

    assert spec == mock_instrument.specification
    mock_spec.return_value.by_name.assert_called_once_with("mari")


@patch("fia_api.core.services.instrument._REPO")
def test_get_specification_by_instrument_name_instrument_missing(mock_repo):
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo.find_one.return_value = None

        with pytest.raises(MissingRecordError):
            get_specification_by_instrument_name("mari")


@patch("fia_api.core.services.instrument._REPO")
@patch("fia_api.core.services.instrument.InstrumentSpecification")
def test_update_specification_for_instrument(mock_spec, mock_repo):
    instrument = Mock()

    mock_repo.find_one.return_value = instrument

    update_specification_for_instrument("mari", {"foo": 1})

    mock_repo.find_one.assert_called_once_with(mock_spec.return_value.by_name.return_value)
    assert instrument.specification == {"foo": 1}
    mock_repo.update_one.assert_called_once_with(instrument)


@patch("fia_api.core.services.instrument._REPO")
def test_update_specification_for_instrument_instrument_missing(mock_repo):
    with patch("fia_api.core.services.instrument.InstrumentSpecification"):
        mock_repo.find_one.return_value = None
        with pytest.raises(MissingRecordError):
            update_specification_for_instrument("mari", {"foo": 1})
