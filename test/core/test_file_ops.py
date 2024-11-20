import io
import random
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import fastapi.exceptions
import pytest
from fastapi import HTTPException
from fastapi.datastructures import Headers
from starlette.datastructures import UploadFile

from fia_api.core.file_ops import read_dir, write_file_from_remote


@pytest.fixture(autouse=True)
def _setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("EXTRAS_DIRECTORY", str(tmp_path))


@pytest.fixture()
def _setup_inst_folder(tmp_path):
    for instrument_folder in sorted(instrument_folders):
        path = tmp_path / instrument_folder
        path.mkdir(parents=True, exist_ok=True)


# To prevent duplicated tests with multiple backends
@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def mock_file():
    file_names = ["test_file_1.txt", "test_file_2.png"]
    files = {
        0: (file_names[0], b"Insert file content here", "text/plain"),
        1: (file_names[1], b"Yet another file", "text/plain"),
    }
    return files[random.randint(0, 1)]  # noqa: S311


instrument_folders = [
    "alf",
    "argus",
    "chipir",
    "chronus",
    "crisp",
    "emu",
    "enginx",
    "gem",
    "hifi",
    "hrpd",
    "imat",
    "ines",
    "inter",
    "iris",
    "larmor",
    "let",
    "loq",
    "maps",
    "mari",
    "merlin",
    "musr",
    "nimrod",
    "offspec",
    "osiris",
    "pearl",
    "polaris",
    "polref",
    "sandals",
    "sans2d",
    "surf",
    "sxd",
    "tosca",
    "vesuvio",
    "wish",
    "zoom",
]


@pytest.mark.usefixtures("_setup_inst_folder")
def test_read_dir(tmp_path):
    """Tests the root folder is readable"""
    response = read_dir(tmp_path)
    assert sorted(response) == instrument_folders


def test_read_dir_handles_io_error(tmp_path):
    path = tmp_path / "test_dir"
    try:
        read_dir(path)
    except Exception as e:
        if type(e) is fastapi.exceptions.HTTPException:
            pytest.raises(fastapi.exceptions.HTTPException)


@pytest.mark.anyio()
async def test_write_files_handles_permission_error(tmp_path, mock_file):
    # Mock UploadFile
    mock_remote_file = MagicMock(spec=UploadFile)
    mock_remote_file.read = AsyncMock(return_value=mock_file[1])
    mock_remote_file.file = io.BytesIO(mock_file[1])

    # Mock local path
    mock_path = AsyncMock()
    mock_path.write_bytes = AsyncMock()
    mock_path.write_bytes.side_effect = PermissionError("Mocked_permission_error")

    # Patch anyio.Path
    with pytest.MonkeyPatch().context() as m:
        m.setattr("anyio.Path", lambda path: mock_path)
        with pytest.raises(HTTPException) as exc_info:
            await write_file_from_remote(mock_remote_file, tmp_path / "permissionerror" / mock_file[0])
        # Exception assertions
        assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
        assert "Permissions denied for the instrument folder" in exc_info.value.detail
    # Mock assertions
    mock_remote_file.read.assert_awaited_once()  # Ensure file was read
    mock_path.write_bytes.assert_awaited_once_with(mock_file[1])  # Ensure file written


@pytest.mark.anyio()
async def test_write_files_handles_file_not_found_error(tmp_path, mock_file):
    path = tmp_path / "not_found"
    thefile = UploadFile(
        filename=mock_file[0],
        size=8626,
        headers=Headers(
            {
                "content-disposition": 'form-data; name="file"; filename="reloads extras.txt"',
                "content-type": "text/plain",
            }
        ),
        file=io.BytesIO(mock_file[1]),
    )

    with pytest.raises(HTTPException) as exc_info:
        await write_file_from_remote(thefile, path / "mock_file.txt")
    assert "FileNotFoundError" in str(exc_info.value)
