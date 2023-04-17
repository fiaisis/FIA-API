"""
Custom Exceptions
"""


class DatabaseError(Exception):
    """
    Database specific error
    """


class MissingRecordError(DatabaseError):
    """
    Record was requested but did not exist
    """


class NonUniqueRecordError(DatabaseError):
    """
    Multiple records were found when only a single was expected
    """


class MissingScriptError(Exception):
    """
    No script could be found on remote or on github, it is likely the instrument does not exist
    """
