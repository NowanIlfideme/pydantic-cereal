"""Error definitions."""


class CerealBaseError(Exception):
    """Base error class for pydantic-cereal."""


class CerealRegistrationError(CerealBaseError):
    """Error during registration."""


class CerealProtocolError(CerealBaseError, TypeError):
    """Error with a reader or writer protocol.

    This is also a TypeError.
    """


class CerealContextError(CerealBaseError):
    """Error with pydantic-cereal context."""
