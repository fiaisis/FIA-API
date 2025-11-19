"""Custom Exceptions"""


class DatabaseError(Exception):
    """Database specific error"""


class MissingRecordError(DatabaseError):
    """Record was requested but did not exist"""


class AuthError(Exception):
    """Raised when there was a problem with authentication or authorisation"""


class NonUniqueRecordError(DatabaseError):
    """Multiple records were found when only a single was expected"""


class MissingScriptError(Exception):
    """No script could be found on remote or on github, it is likely the instrument does not exist"""


class UnsafePathError(Exception):
    """A path was given that is potentially unsafe and could lead to directory traversal"""


class JobRequestError(ValueError):
    """The job request was malformed"""


class NoFilesAddedError(Exception):
    """
    Raised when no files could be added to the ZIP response.
    :param missing_files: list of "job_id/filename" strings that were not found.
    """

    def __init__(self, missing_files: list[str]) -> None:
        self.missing_files = missing_files
        super().__init__("None of the requested files could be found.")

#exceptions for file_ops.py
class UploadPermissionsError(Exception):
    """The appropriate permissions to access files has not been provided"""

class ReadDirError(Exception):
    """There was an error returning the files"""

class UploadFileError(Exception):
    """There was an error uploading the file"""

#exceptions for utility.py

class InvalidPathError(Exception):
    """Invalid path being accessed and file not found"""


class GithubAPIRequestError(Exception):
    """Github API request failed with status code"""


class BadRequestError(Exception):
    """Bad request was made"""


#exceptions for tokens.py

class InvalidTokenError(Exception):
    """Invalid or expired token or invalid API key"""


class ServiceUnavailable(Exception):
    """Service unavailable"""