"""User-facing classes."""

import json
import uuid
import warnings
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, List, Optional, Tuple, Type, TypeVar, Union

from fsspec import AbstractFileSystem, get_fs_token_paths
from pydantic import (
    BaseModel,
    SerializerFunctionWrapHandler,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
)
from pydantic.functional_serializers import WrapSerializer
from pydantic.functional_validators import WrapValidator
from pydantic.json_schema import WithJsonSchema
from typing_extensions import Annotated, Self
from upath import UPath

from ._metadata import CerealInfo, ImportString, cereal_meta_schema
from ._path_utils import append_path_parts, ensure_empty_dir
from ._protocols import (
    CerealReader,
    CerealWriter,
    ReaderLike,
    WriterLike,
    normalize_reader,
    normalize_writer,
)
from ._utils import get_import_string, import_object
from .errors import CerealContextError
from .version import __version__

T = TypeVar("T")
TModel = TypeVar("TModel", bound=BaseModel)


__all__ = ["Cereal", "CerealReader", "CerealWriter", "cereal_meta_schema"]


class CerealContext(AbstractContextManager):
    """Serialization context.

    This is managed by the [`Cereal`][pydantic_cereal.Cereal] class - users shouldn't use this directly!
    """

    def __init__(
        self,
        cereal: "Cereal",
        target_path: Union[UPath, Path, str],
        fs: Optional[AbstractFileSystem] = None,
    ) -> None:
        assert isinstance(cereal, Cereal)
        if fs is None:
            if isinstance(target_path, str):
                fs, _, paths = get_fs_token_paths(target_path)
                inner_path = paths[-1]
            elif isinstance(target_path, Path) and not isinstance(target_path, UPath):
                fs, _, paths = get_fs_token_paths(f"file://{target_path}")
                inner_path = paths[-1]
            elif isinstance(target_path, UPath):
                fs = target_path.fs
                inner_path = target_path.path
            else:
                raise TypeError("'target_path' must be a 'str', 'Path' or 'UPath'")
        else:
            assert isinstance(target_path, str)
            inner_path = target_path

        # Double-check
        assert isinstance(fs, AbstractFileSystem)
        assert isinstance(inner_path, str)

        self._target_path = inner_path
        self._fs: AbstractFileSystem = fs
        self._cereal = cereal

    @property
    def target_path(self) -> str:
        """Target path of context."""
        return self._target_path

    @property
    def fs(self) -> AbstractFileSystem:
        """File system to be used for target path."""
        return self._fs

    @property
    def cereal(self) -> "Cereal":
        """Parent of the context."""
        return self._cereal

    def __enter__(self: Self) -> Self:
        """Use as a context manager."""
        self.cereal._push_context(self)
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Any,
    ) -> Optional[bool]:
        """Exit from the context manager."""
        self.cereal._pop_context(self)
        return super().__exit__(__exc_type, __exc_value, __traceback)


TType = TypeVar("TType", bound=type)


class Cereal(object):
    """Main serialization object.

    Usage
    -----
    To set up, create a global `cereal` variable:

    ```python
    from pydantic_cereal import Cereal

    cereal = Cereal()  # global variable
    ```

    Use [`cereal.wrap_type()`][pydantic_cereal.Cereal.wrap_type] to "register" readers and writers
    into a new `Annotated` type.
    """

    # Annotation API

    def wrap_type(self, type_: Type[T], reader: ReaderLike, writer: WriterLike) -> Type[T]:
        """Wrap a type with reader and writer metadata, for use with Pydantic."""
        (f_reader, s_reader) = self._normalize_reader(reader=reader)
        (f_writer, s_writer) = self._normalize_writer(writer=writer)

        def f_serializer(v: Any, nxt: SerializerFunctionWrapHandler) -> CerealInfo:
            """Serialize by writing and returning metadata."""
            # Ensure we are in a context (or just fall back on default behavior)
            if self.active_context is None:
                warnings.warn(
                    "Attempting to use pydantic-cereal outside of the context. Using default serializer."
                )
                return nxt(v)

            # Write object
            obj_upath = self._write_obj(v, f_writer)
            obj_path = str(obj_upath)

            return CerealInfo(
                cereal_version=__version__,
                cereal_writer=s_writer,
                cereal_reader=s_reader,
                object_path=obj_path,
                # maybe other metadata?
            )

        serializer = WrapSerializer(f_serializer, return_type=CerealInfo, when_used="always")

        def f_validator(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> Any:
            """Validate by loading from context."""
            if self.active_context is None:
                # Attempting to use pydantic-cereal outside of the context. Using default validator
                return handler(v)
            # We are in the context, so try to load it.

            # Try parsing `v` as metadata. If we fail, assume that validator can handle it.
            if info.mode == "json":
                assert isinstance(v, str), "In JSON mode the input must be a string!"
                try:
                    cereal_meta = TypeAdapter(CerealInfo).validate_json(v)
                    loaded = self._load_from_meta(cereal_meta=cereal_meta)
                except ValidationError:
                    loaded = v
            elif info.mode == "python":
                try:
                    cereal_meta = TypeAdapter(CerealInfo).validate_python(v)
                    loaded = self._load_from_meta(cereal_meta=cereal_meta)
                except ValidationError:
                    loaded = v
            else:
                raise NotImplementedError(f"Unknown parsing mode: {info.mode!r}")
            # Pass to original validator
            res = handler(loaded)
            return res

        validator = WrapValidator(f_validator)

        res = Annotated[
            type_,  # type: ignore
            serializer,
            validator,
            WithJsonSchema(cereal_meta_schema),
        ]
        return res  # type: ignore

    # I/O API

    def write_model(
        self,
        model: BaseModel,
        target_path: Union[UPath, Path, str],
        fs: Optional[AbstractFileSystem] = None,
    ) -> str:
        """Write the pydantic.BaseModel to the path.

        TODO
        ----
        - Add JSON options.
        - Write YAML metadata instead?
        """
        with self.context(target_path=target_path, fs=fs):
            # Create saving directory
            fs = self.fs
            targ_path = ensure_empty_dir(fs, self.target_path)

            # Write model (as JSON) with extra 'class' keyword
            # NOTE: This will write all wrapped types too!
            model_dict = model.model_dump(mode="json")
            if "class" in model_dict:
                raise ValueError("Key 'class' is reserved for pydantic-cereal.")
            model_dict["class"] = get_import_string(type(model))
            model_json = json.dumps(model_dict, indent=2)
            with fs.open(append_path_parts(fs, targ_path, "model.json"), mode="w") as f:
                f.write(model_json)
            # Write schema (as JSON)
            model_j_schema = json.dumps(model.model_json_schema(), indent=2)
            with fs.open(append_path_parts(fs, targ_path, "model.schema.json"), mode="w") as f:
                f.write(model_j_schema)
            # FIXME: We need to also write metadata somewhere, such as "what object is this?"...
        return targ_path

    def read_model(
        self,
        target_path: Union[UPath, Path, str],
        fs: Optional[AbstractFileSystem] = None,
        *,
        supercls: Type[TModel] = BaseModel,  # type: ignore
    ) -> TModel:
        """Read a pydantic.BaseModel from the path."""
        if not issubclass(supercls, BaseModel):
            raise TypeError(
                f"Can only read Pydantic models, but {supercls!r} is not derived from BaseModel."
            )
        with self.context(target_path=target_path, fs=fs):
            fs = self.fs
            targ_path = self.target_path
            # Load raw data
            with fs.open(append_path_parts(fs, targ_path, "model.json"), mode="r") as f:
                model_raw = json.load(f)
            # Get model class
            assert isinstance(model_raw, dict)
            model_import_str = model_raw.get("class")
            if model_import_str is None:
                raise ValueError("No 'class' field available - cannot figure out type.")
            model_cls = import_object(model_import_str)
            assert issubclass(model_cls, supercls)
            # Parse as model
            res = TypeAdapter(model_cls).validate_python(model_raw)
            return res

    # Creation

    def __init__(self) -> None:
        self._context_stack: List[CerealContext] = []

    def __repr__(self) -> str:
        """Representation."""
        return type(self).__qualname__ + "()"

    # Internal API

    def context(
        self, target_path: Union[UPath, Path, str], fs: Optional[AbstractFileSystem]
    ) -> CerealContext:
        """Create a writing context (usable via `with` statement)."""
        return CerealContext(self, target_path=target_path, fs=fs)

    @property
    def active_context(self) -> Optional[CerealContext]:
        """The currently active context."""
        if len(self._context_stack) == 0:
            return None
        return self._context_stack[-1]

    def _push_context(self, ctx: CerealContext) -> None:
        """Add a context to the stack and make it active."""
        if ctx in self._context_stack:
            raise CerealContextError("Context is already in stack - can't re-enter!")
        self._context_stack.append(ctx)

    def _pop_context(self, ctx: CerealContext) -> None:
        """Remove an active context from the stack."""
        if ctx is not self.active_context:
            raise CerealContextError("Context is not the active one - can't exit.")
        self._context_stack.pop()

    @property
    def fs(self) -> AbstractFileSystem:
        """Current filesystem."""
        if self.active_context is None:
            raise CerealContextError("No context is active - no current filesystem.")
        return self.active_context.fs

    @property
    def target_path(self) -> str:
        """Working directory."""
        if self.active_context is None:
            raise CerealContextError("No context is active - no working directory.")
        return self.active_context.target_path

    def _generate_filename(self, obj: Any) -> str:
        """Generate a file name for an object.

        TODO
        ------------
        Improve by using JSON-path-like?
        """
        return str(uuid.uuid4()).replace("-", "")

    def _write_obj(self, obj: Any, writer: CerealWriter) -> str:
        """Write object, returning its relative path."""
        if self.active_context is None:
            raise CerealContextError("Context not active - aborting write.")
        filename = self._generate_filename(obj)

        fs = self.fs
        write_path = append_path_parts(fs, self.target_path, filename)
        writer(obj, self.fs, write_path)
        return filename

    def _load_from_meta(self, cereal_meta: CerealInfo) -> Any:
        """Load an object from metadata."""
        f_reader, _ = self._normalize_reader(cereal_meta.cereal_reader)

        fs = self.fs
        path = append_path_parts(fs, self.target_path, cereal_meta.object_path)
        return f_reader(fs, path)

    # Helpers

    @classmethod
    def _normalize_reader(cls, reader: ReaderLike) -> Tuple[CerealReader, ImportString]:
        """Normalize reader, writer to their objects and paths."""
        f_reader = normalize_reader(reader)
        s_reader = get_import_string(f_reader)
        return (f_reader, s_reader)

    @classmethod
    def _normalize_writer(cls, writer: WriterLike) -> Tuple[CerealWriter, ImportString]:
        """Normalize reader, writer to their objects and paths."""
        f_writer = normalize_writer(writer)
        s_writer = get_import_string(f_writer)
        return (f_writer, s_writer)
