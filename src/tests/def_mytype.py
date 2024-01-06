"""Define MyType and custom models."""
# Custom object type

from fsspec import AbstractFileSystem
from pydantic import BaseModel, ConfigDict

from .common import cereal


class MyType(object):
    """My custom type, which isn't a Pydantic model."""

    def __init__(self, value: str):
        """Initialize the object."""
        self.value = str(value)

    def __repr__(self) -> str:
        """Represent the string."""
        return f"MyType({self.value})"

    def __eq__(self, rhs: object) -> bool:
        """Equality testing (required for assert)."""
        if not isinstance(rhs, MyType):
            return NotImplemented
        return rhs.value == self.value


def my_reader(fs: AbstractFileSystem, path: str) -> MyType:
    """Read a MyType from an fsspec URI."""
    return MyType(value=fs.read_text(path))  # type: ignore


def my_writer(obj: MyType, fs: AbstractFileSystem, path: str) -> None:
    """Write a MyType object to an fsspec URI."""
    fs.write_text(path, obj.value)


MyWrappedType = cereal.wrap_type(MyType, reader=my_reader, writer=my_writer)


class MyModel(BaseModel):
    """My custom Pydantic model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Pydantic configuration
    fld: MyWrappedType
