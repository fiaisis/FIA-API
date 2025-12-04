import io
import os
import zipfile
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from fia_api.core.models import JobType
from test.e2e.constants import STAFF_HEADER, USER_HEADER
from test.e2e.test_core import client


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_success(mock_post, mock_get_experiments):
    """Test that a valid request with a job of type 'AUTOREDUCTION' returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_invalid_file(mock_post, mock_get_experiments):
    """Test that a 404 is returned when an invalid file name is supplied."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/invalid_filename.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_unauthorized(mock_post, mock_get_experiments):
    """Test that a request without authentication returns 403."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe")

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_invalid_job(mock_post):
    """Test that a 404 is returned for an invalid job ID."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    response = client.get("/job/99999/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_no_owner(mock_post, mock_get_experiments, mock_get_job):
    """Test that an internal server error is returned with when a job has the type 'AUTOREDUCED' and the owner is
    missing."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner = None

    response = client.get("/job/5001/filename/test.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_experiment_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that an internal server error is returned with when a job has the type 'AUTOREDUCED' and the experiment
    number is missing."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.experiment_number = None

    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple(mock_post, mock_get_experiments, mock_get_job):
    """Test that a valid request with a job of type 'SIMPLE' returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.job_type = JobType.SIMPLE
    mock_get_job.return_value.owner.experiment_number = 20024
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple_and_experiment_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that a valid request with a job of type 'SIMPLE' and no experiment number returns a file."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = 20024
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/octet-stream"


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_simple_and_experiment_and_user_number_missing(mock_post, mock_get_experiments, mock_get_job):
    """Test that an missing record error is returned when the job type is 'SIMPLE' and there is no experiment number
    and user number."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = None
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE

    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@patch("fia_api.core.services.job.find_file_user_number")
@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_file_missing_filepath(mock_post, mock_get_experiments, mock_get_job, mock_find_file):
    """Test that a file not found error is returned in the event the filepath is None."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    mock_get_job.return_value.owner.user_number = 1234
    mock_get_job.return_value.owner.experiment_number = None
    mock_get_job.return_value.job_type = JobType.SIMPLE
    mock_find_file.return_value = None
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.core.auth.tokens.requests.post")
def test_download_invalid_user_perms(mock_post):
    """Test that a user trying to download a file that doesn't match their credentials returns a 403 status code."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.FORBIDDEN
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=USER_HEADER)

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.routers.jobs.get_job_by_id")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_valid_user_perms(mock_post, mock_get_job):
    """Test that a user trying to download a file that does match their credentials returns a 200 status code."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_job.return_value.owner.experiment_number = 20024
    mock_get_job.return_value.instrument.instrument_name = "MARI"
    response = client.get("/job/5001/filename/MAR29531_10.5meV_sa.nxspe", headers=USER_HEADER)

    assert response.status_code == HTTPStatus.OK


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_success(mock_post, mock_get_experiments):
    """Test that a valid request returns a zip file containing multiple files."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    payload = {"5001": ["MAR29531_10.5meV_sa.nxspe", "MAR29531_10.5meV_sa_copy.nxspe"]}
    response = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == "attachment; filename=reduction_files.zip"

    # Validate the contents of the zip
    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as zipf:
        names = zipf.namelist()
        assert "5001/MAR29531_10.5meV_sa.nxspe" in names
        assert "5001/MAR29531_10.5meV_sa_copy.nxspe" in names


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_with_invalid_file(mock_post, mock_get_experiments):
    """Test that only valid files are zipped when one filename is invalid."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    payload = {"5001": ["MAR29531_10.5meV_sa.nxspe", "nonexistent_file.nxspe"]}
    response = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/zip"

    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as zipf:
        names = zipf.namelist()
        assert "5001/MAR29531_10.5meV_sa.nxspe" in names
        assert "5001/nonexistent_file.nxspe" not in names


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_unauthorized(mock_post, mock_get_experiments):
    """Test that a request without authentication returns 403 for zip download."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    payload = {"5001": ["MAR29531_10.5meV_sa.nxspe"]}
    response = client.post("/job/download-zip", json=payload)

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_invalid_job(mock_post):
    """Test that a 404 is returned for an invalid job ID in zip download."""
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK

    payload = {"99999": ["MAR29531_10.5meV_sa.nxspe"]}
    response = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_partial_missing_returns_200(mock_post, mock_get_experiments):
    """
    When some files are missing: return 200, include only existing files in the ZIP,
    and set x-missing-files* headers.
    """
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]

    payload = {
        "5001": [
            "MAR29531_10.5meV_sa.nxspe",
            "does_not_exist_1.nxspe",
        ]
    }
    resp = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["content-type"] == "application/zip"
    assert resp.headers["content-disposition"] == "attachment; filename=reduction_files.zip"
    assert resp.headers.get("x-missing-files-count") == "1"
    assert "5001/does_not_exist_1.nxspe" in resp.headers.get("x-missing-files", "")

    # ZIP should contain only the existing file
    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
        names = zf.namelist()
        assert "5001/MAR29531_10.5meV_sa.nxspe" in names
        assert "5001/does_not_exist_1.nxspe" not in names


@patch("fia_api.core.services.job.get_experiments_for_user_number")
@patch("fia_api.core.auth.tokens.requests.post")
def test_download_zip_all_missing_returns_404(mock_post, mock_get_experiments):
    """
    When ALL requested files are missing: return 404 via NoFilesAddedError handler
    and include x-missing-files* headers plus a structured JSON body.
    """
    os.environ["CEPH_DIR"] = str((Path(__file__).parent / ".." / "test_ceph").resolve())
    mock_post.return_value.status_code = HTTPStatus.OK
    mock_get_experiments.return_value = [1820497]
    payload = {
        "5001": [
            "does_not_exist_1.nxspe",
            "does_not_exist_2.nxspe",
        ]
    }

    resp = client.post("/job/download-zip", json=payload, headers=STAFF_HEADER)

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.headers.get("content-type") == "application/json"

    assert resp.headers.get("x-missing-files-count") == "2"
    missing_hdr = resp.headers.get("x-missing-files", "")
    assert "5001/does_not_exist_1.nxspe" in missing_hdr
    assert "5001/does_not_exist_2.nxspe" in missing_hdr

    body = resp.json()
    assert body["detail"] == "None of the requested files could be found."
    assert body["missing_files_count"] == 2  # noqa: PLR2004
    assert set(body["missing_files"]) == {
        "5001/does_not_exist_1.nxspe",
        "5001/does_not_exist_2.nxspe",
    }
