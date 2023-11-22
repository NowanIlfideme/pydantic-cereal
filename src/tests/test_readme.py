"""Tests for README/Index examples.

The "global" `cereal` object here is only global to this module, which
"""

from pydantic import BaseModel, ConfigDict
from upath import UPath  # based on `fsspec`, used for `pathlib.Path`-like interface

from pydantic_cereal import Cereal

cereal = Cereal()  # This is a global variable


class MyType(object):
    """My custom type, which isn't a Pydantic model."""

    def __init__(self, value: str):
        """Initialize the object."""
        self.value = str(value)

    def __repr__(self) -> str:
        """Represent the string."""
        return f"MyType({self.value})"


# Create reader and writer from an fsspec URI


def my_reader(uri: str) -> MyType:
    """Read a MyType from an fsspec URI."""
    return MyType(value=UPath(uri).read_text())


def my_writer(obj: MyType, uri: str) -> None:
    """Write a MyType object to an fsspec URI."""
    UPath(uri).write_text(obj.value)


# "Register" this type with pydantic-cereal
MyWrappedType = cereal.wrap_type(MyType, reader=my_reader, writer=my_writer)
# NOTE: Your type isn't modified, we just apply `Annotated` with a custom serializer and validator


# Use the wrapped type as the fields of your Pydantic model


class MyModel(BaseModel):
    """My custom Pydantic model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Pydantic configuration
    fld: MyWrappedType


def test_readme(random_path: str):
    """Test example in README/Index.

    Note
    ----
    For pytest, we must add a random path to avoid flakiness.
    """
    mdl = MyModel(fld=MyType("my_field"))

    # We can save the whole model to an fsspec URI, such as this MemoryFileSystem
    uri = f"memory://my_model/{random_path}"
    cereal.write_model(mdl, uri)

    # And we can read it back later
    obj = cereal.read_model(uri)
    assert isinstance(obj, MyModel)
    assert isinstance(obj.fld, MyType)
