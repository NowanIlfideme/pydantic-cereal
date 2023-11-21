# `pydantic-cereal`

## Advanced serialization for Pydantic models

[Pydantic](https://docs.pydantic.dev/latest/) is the most widely used data validation library for Python.
It uses type hints/type annotations to define data models and has quite a nice "feel" to it.
Pydantic V2 was [released in June 2023](https://docs.pydantic.dev/2.0/blog/pydantic-v2-final/) and
brings many changes and improvements, including a
[new Rust-based engine for serializing and validating data](https://github.com/pydantic/pydantic-core).

This package, `pydantic-cereal`, is a small extension package that enables users to serialize Pydantic
models with "arbitrary" (non-JSON-fiendly) types to "arbitrary" file-system-like locations.
It uses [`fsspec`](https://filesystem-spec.readthedocs.io/en/latest/) and
[`universal_pathlib`](https://pypi.org/project/universal-pathlib/) to support generic file systems.
Writing a custom writer (serializer) and reader (loader) with `fsspec` URIs is quite straightforward.

See the [full documentation here](https://pydantic-cereal.readthedocs.io/).

## Usage Example

For most uses, you only need the `Cereal` class and `fsspec` or `upath`.

```python
from upath import UPath  # based on `fsspec`, used for `pathlib.Path`-like interface
from pydantic import BaseModel, ConfigDict
from pydantic_cereal import Cereal

cereal = Cereal()  # This is a global variable


class MyType(object):
    """My custom type, which isn't a Pydantic model."""

    def __init__(self, value: str):
        self.value = str(value)

    def __repr__(self) -> str:
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

    config = ConfigDict(arbitrary_types_allowed=True)
    fld: MyWrappedType


mdl = MyModel(fld=MyType("my_field"))

# We can save the whole model to an fsspec URI, such as this MemoryFileSystem
cereal.write_model(mdl, "memory://my_model")

# And we can read it back later
obj = cereal.read_model("memory://my_model")
assert isinstance(obj, MyModel)
assert isinstance(obj.fld, MyType)
```

For more detailed discussion, see the [minimal pure-Python example](./docs/examples/minimal.ipynb) or
the [Pandas dataframe example](./docs/examples/pandas.ipynb)
