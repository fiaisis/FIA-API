"""Custom Exceptions"""


class DatabaseError(Exception):
    """Database specific error"""


class MissingRecordError(DatabaseError):
    """Record was requested but did not exist"""


class AuthenticationError(Exception):
    """Raised when there was a problem with authentication or authorisation"""


class NonUniqueRecordError(DatabaseError):
    """Multiple records were found when only a single was expected"""


class MissingScriptError(Exception):
    """No script could be found on remote or on github, it is likely the instrument does not exist"""


class UnsafePathError(Exception):
    """A path was given that is potentially unsafe and could lead to directory traversal"""


class JobRequestError(ValueError):
    """The job request was malformed"""
