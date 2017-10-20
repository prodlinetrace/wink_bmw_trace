class PLCAPIException(Exception):
    """
    Base class for all errors
    """
    pass


class NotFound(PLCAPIException):
    """
    Resource cannot be found
    """
    pass


class UnknownDB(KeyError, NotFound):
    """
    PLC Controller does not recognize the DB requested.
    """
    pass


class UnknownStation(KeyError, NotFound):
    """
    PLC Controller does not recognize the Station requested.
    """
    pass


class UnknownSN(KeyError, NotFound):
    """
    PLC Controller does not recognize requested Serial Number.
    """
    pass


class PLCSendRcvTimeOut(PLCAPIException):
    """
    Polling Send and Recieve timeout.
    """
    pass
