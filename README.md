# `pydantic-cereal`

## Advanced serialization for Pydantic models

[Pydantic](https://docs.pydantic.dev/latest/) is the most widely used data validation library for Python.
It uses type hints/type annotations to define data models and has quite a nice "feel" to it.
Pydantic V2 was [released in June 2023](https://docs.pydantic.dev/2.0/blog/pydantic-v2-final/) and
brings many changes and improvements, including a
[new Rust-based engine for serializing and validating data](https://github.com/pydantic/pydantic-core).

This package, `pydantic-cereal`, is a small extension package that enables users to serialize Pydantic
models with "arbitrary" (non-JSON-fiendly) types to "arbitrary" file-system-like locations.
It uses [`fsspec`](https://filesystem-spec.readthedocs.io/en/latest/) to support generic file systems.
Writing a custom writer (serializer) and reader (loader) with `fsspec` URIs is quite straightforward.
You can also use [`universal-pathlib`](https://pypi.org/project/universal-pathlib/)'s
`UPath` with `pydantic-cereal`.

📘 See the [full documentation here](https://pydantic-cereal.readthedocs.io/). 📘

## Usage Example

See the [minimal pure-Python example](./docs/examples/minimal.ipynb) to learn how to wrap your own type.
Below is a preview of this example.

```python
from fsspec import AbstractFileSystem
from pydantic import BaseModel, ConfigDict

from pydantic_cereal import Cereal

cereal = Cereal()  # This is a global variable


# Create and "register" a custom type

class MyType(object):
    """My custom type, which isn't a Pydantic model."""

    def __init__(self, value: str):
        self.value = str(value)

    def __repr__(self) -> str:
        return f"MyType({self.value})"


def my_reader(fs: AbstractFileSystem, path: str) -> MyType:
    """Read a MyType from an fsspec URI."""
    return MyType(value=fs.read_text(path))  # type: ignore


def my_writer(obj: MyType, fs: AbstractFileSystem, path: str) -> None:
    """Write a MyType object to an fsspec URI."""
    fs.write_text(path, obj.value)

MyWrappedType = cereal.wrap_type(MyType, reader=my_reader, writer=my_writer)


# Use type within Pydantic model

class MyModel(BaseModel):
    """My custom Pydantic model."""

    config = ConfigDict(arbitrary_types_allowed=True)  # Pydantic configuration
    fld: MyWrappedType


mdl = MyModel(fld=MyType("my_field"))

# We can save the whole model to an fsspec URI, such as this MemoryFileSystem
uri = "memory://my_model"
cereal.write_model(mdl, uri)

# And we can read it back later
obj = cereal.read_model(uri)
assert isinstance(obj, MyModel)
assert isinstance(obj.fld, MyType)
```

For wrapping 3rd-party libraries, see the [Pandas dataframe example](./docs/examples/pandas.ipynb).
