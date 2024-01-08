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

## Usage Examples

See the [minimal pure-Python example](./examples/minimal.ipynb) to learn how to wrap your own type.
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

For wrapping 3rd-party libraries, see the [Pandas dataframe example](./examples/pandas.ipynb).

## Key Concepts

The [`Cereal`][pydantic_cereal.Cereal] class is the main interface, handling type registration and I/O.
You should define one global object of this type, i.e. `cereal = Cereal()` within your modules.

You can save or load Pydantic models via `cereal` to any `fsspec` URI, `universal-pathlib` `UPath` or -
for more complicated cases - to a path within a pre-made `fsspec` file system.
The serialization format is a *directory* under the given path, containing the `model.json` (main fields
and metadata), `model.schema.json` (JSON schema for your Pydantic model, as a nice-to-have) and
the serialized objects that are *not* representable in JSON.

In order for `cereal` and `Pydantic` to know how to serialize your non-JSON-compatible type, you must:

1. wrap your type with [`cereal.wrap_type(type, reader, writer)`][pydantic_cereal.Cereal.wrap_type];
2. specify[`arbitrary_types_allowed`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.arbitrary_types_allowed)
   in your [Pydantic model configuration](https://docs.pydantic.dev/latest/concepts/config/);
3. add the *wrapped* type as fields in your Pydantic model;
4. use [`cereal.write_model(mdl, path)`][pydantic_cereal.Cereal.write_model] to write your model object
   to the given fsspec path.

!!! note

    You can easily wrap types from 3rd-party classes. Since you don't need to re-define the type, it will
    "just work" outside of the Pydantic models.

    You can even specify different serialization mechanisms for different fields that have the same type;
    just wrap your types multiple times with different readers/writers.

## How It Works

Under the hood, `pydantic-cereal` uses the new
[functional serializers](https://docs.pydantic.dev/latest/concepts/serialization/#custom-serializers)
that are available in Pydantic V2 and use
[`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)
(or `typing_extensions.Annotated`).

!!! note

    When you use `wrap_type`, the only "wrapping" done is adding metadata via
    [`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated).
    The class itself isn't changed, and nothing will change in terms of your code, IDE or type checkers!

The [`Cereal`][pydantic_cereal.Cereal] class uses a context to convert the objects-to-write into
JSON-compatible metadata, then call the respective `writer`
([`CerealWriter`-compatible][pydantic_cereal.CerealWriter]) functions.

When reading, the `Cereal` object imports your Pydantic model class and any `reader`
([`CerealReader`-compatible][pydantic_cereal.CerealReader]) functions for your wrapped types,
then reads the objects from the `fsspec` URIs, and plugs them into your model.

## Limitations

1. Your `cereal` object doesn't necessarily have to be a global, but the same instance must be
   used to both *register* your model type and *write* your object (and ideally *read* too).
2. You can't define your types or Pydantic model inside a function, because `pydantic-cereal` relies on
   importing your type by dotted name (`package.module.MyType`), and we can't import local variables.
   Instead, define it in a top-level module, then import it.
3. When running from the REPL or in a Jupyter notebook, the module name for your class definitions
   will be `__main__`. This means your saved objects will only be loadable in the same kind of session.
   We strongly recommend you move your code to a *Python package* structure ASAP to avoid issues.
