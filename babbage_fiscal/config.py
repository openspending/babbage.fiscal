import os

from sqlalchemy import create_engine

_engine = None
_connection_string = os.environ['FISCAL_PACKAGE_ENGINE']


def _set_connection_string(connection_string):
    global _connection_string
    global _engine
    if _connection_string != connection_string:
        _connection_string = connection_string
        _engine = None


def get_connection_string():
    return _connection_string


def get_engine():
    """Return engine singleton"""
    global _engine
    if _engine is None:
        _engine = create_engine(_connection_string)

    return _engine
