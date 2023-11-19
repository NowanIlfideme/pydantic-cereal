"""Error definitions."""


class PydanticCerealError(Exception):
    """Base error class for pydantic-cereal."""


class RegistrationError(PydanticCerealError):
    """Error during registration."""


class CerealProtocolError(PydanticCerealError, TypeError):
    """Error with a reader or writer protocol.

    This is also a TypeError.
    """


class CerealContextError(PydanticCerealError):
    """Error with pydantic-cereal context."""
