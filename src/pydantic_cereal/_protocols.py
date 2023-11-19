"""Protocols and helpers for reader/writier objects."""

import inspect
from abc import abstractmethod
from typing import Any, Protocol, TypeVar, Union, runtime_checkable

from ._utils import import_object
from .errors import CerealProtocolError

__all__ = [
    "CerealReader",
    "CerealWriter",
    "ReaderLike",
    "WriterLike",
    "normalize_reader",
    "normalize_writer",
]


T_read = TypeVar("T_read", covariant=True)
T_write = TypeVar("T_write", contravariant=True)


@runtime_checkable
class CerealReader(Protocol[T_read]):
    """Reader class for a particular type."""

    @abstractmethod
    def __call__(self, uri: str) -> T_read:
        """Read data from the given URI."""


@runtime_checkable
class CerealWriter(Protocol[T_write]):
    """Writer class for a particular type."""

    @abstractmethod
    def __call__(self, obj: T_write, uri: str) -> Any:
        """Write data to the given URI."""


ReaderLike = Union[CerealReader, str]
WriterLike = Union[CerealWriter, str]


def normalize_reader(reader: ReaderLike) -> CerealReader:
    """Ensure the object passed is a reader."""
    # Load reader, if passed as string
    if isinstance(reader, str):
        reader = import_object(reader)

    # Ensure callable
    if not callable(reader):
        raise CerealProtocolError(
            "Reader must be a function or callable (or a string that imports as such)."
        )

    # Check signature
    sig = inspect.signature(reader)
    try:
        sig.bind("uri")
    except TypeError as why:
        raise CerealProtocolError(f"Reader must be callable with a URI, got signature: {sig!s}") from why
    # TODO: More checking?
    return reader


def normalize_writer(writer: WriterLike) -> CerealWriter:
    """Ensure the object passed is a writer."""
    # Load writer, if passed as string
    if isinstance(writer, str):
        writer = import_object(writer)

    # Ensure callable
    if not callable(writer):
        raise CerealProtocolError(
            "Writer must be a function or callable (or a string that imports as such)."
        )

    # Check signature
    sig = inspect.signature(writer)
    try:
        sig.bind("obj", "uri")
    except TypeError as why:
        raise CerealProtocolError(
            f"Writer must be callable with an object URI, got signature: {sig!s}"
        ) from why
    # TODO: More checking?
    return writer
