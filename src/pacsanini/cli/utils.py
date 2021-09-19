"""Utility methods to facilitate usage of the pacsanini tool from the
command line.
"""
import re


SUPPORTED_DB_DIALECTS = [
    re.compile(r"postgresql(\+[\w\d]+)?://"),
    re.compile(r"mysql(\+[\w\d]+)?://"),
    re.compile(r"mariadb(\+[\w\d]+)?://"),
    re.compile(r"oracle(\+[\w\d]+)?://"),
    re.compile(r"sqlite://"),
]


def is_db_uri(uri: str) -> bool:
    """Return true if the URI is for a known database. False
    otherwise (eg: it is a file path).
    """
    uri_lower = uri.lower()
    for dialect in SUPPORTED_DB_DIALECTS:
        if dialect.match(uri_lower):
            return True
    return False
