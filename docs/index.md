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

## Usage Example

For most uses, you only need the [`Cereal`][pydantic_cereal.Cereal] class and `fsspec` or `upath`.

```python
from fsspec import AbstractFileSystem
from pydantic import BaseModel, ConfigDict

from pydantic_cereal import Cereal

cereal = Cereal()  # This is a global variable


class MyType(object):
    """My custom type, which isn't a Pydantic model."""

    def __init__(self, value: str):
        self.value = str(value)

    def __repr__(self) -> str:
        return f"MyType({self.value})"
```

!!! warning

    There are some [limitations][limitations] on where you can define your Pydantic models.

```python
# Create reader and writer from an fsspec filesystem and path


def my_reader(fs: AbstractFileSystem, path: str) -> MyType:
    """Read a MyType from an fsspec URI."""
    return MyType(value=fs.read_text(path))  # type: ignore


def my_writer(obj: MyType, fs: AbstractFileSystem, path: str) -> None:
    """Write a MyType object to an fsspec URI."""
    fs.write_text(path, obj.value)


# "Register" this type with pydantic-cereal
MyWrappedType = cereal.wrap_type(MyType, reader=my_reader, writer=my_writer)
# NOTE: Your type isn't modified, we just apply `Annotated` with a custom serializer and validator


# Use the wrapped type as the fields of your Pydantic model

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

For more detailed discussion, see the [minimal pure-Python example](./examples/minimal.ipynb) or
the [Pandas dataframe example](./examples/pandas.ipynb)

## How It Works

Under the hood, `pydantic-cereal` uses the new
[functional serializers](https://docs.pydantic.dev/latest/concepts/serialization/#custom-serializers)
that are available in Pydantic V2 and use
[`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)
(or `typing_extensions.Annotated`).

The [`Cereal`][pydantic_cereal.Cereal] class uses a context to convert the objects-to-write into
JSON-compatible metadata, and call the `writer` function.

## Limitations

1. Your `cereal` object doesn't necessarily have to be a global, but the same instance must be
   used to both *register* your model type and *write*/*read* your object.
2. You can't define your Pydantic model inside a function, because `pydantic-cereal` relies on
   importing your type, and we can't import local variables.
   Instead, define it in a top-level module, then import it.
