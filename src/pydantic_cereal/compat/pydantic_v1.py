"""Wrappers for Pydantic v1.X compatibility."""

if True:
    import pydantic

    assert pydantic.__version__ < "2"

from inspect import isabstract
from typing import Any

from pydantic.config import BaseConfig
from pydantic.fields import ModelField
from pydantic.main import BaseModel
from pydantic.validators import find_validators


def is_pydantic_arbitrary_type(type_: type[Any]) -> bool:
    """Checks if a type is 'arbitrary' i.e. not natively supported by Pydantic.

    There's no explicit list of "supported types", only a bunch of checks, so we use `find_validators`.
    The default config has `arbitrary_types_allowed = false`.
    """
    try:
        list(find_validators(type_, BaseConfig))
        return False
    except RuntimeError:
        return True


def get_pydantic_arbitrary_fields(model: BaseModel) -> dict[str, ModelField]:
    """Gets the 'arbitrary' fields from a Pydantic model."""
    return {name: fld for name, fld in model.__fields__.items() if is_pydantic_arbitrary_type(fld.type_)}


class CerealModel(BaseModel):
    """Pydantic model with advanced serialization enabled.

    This also changes some model config options.
    """

    class Config(BaseConfig):
        """Cereal model config defaults."""

        # Pydantic configuration
        arbitrary_types_allowed = True
        smart_union = True
        validate_assignment = True
        # validate_all?

        # Do we need our own configuration?

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if isabstract(cls):
            # TODO: Register class?
            pass

    @property
    def __arbitrary_fields__(self) -> dict[str, ModelField]:
        """Returns arbitrary fields of this model."""
        return get_pydantic_arbitrary_fields(self)

    @property
    def __pure_fields__(self) -> dict[str, ModelField]:
        """Returns 'pure' pydantic-compatible fields of this model."""
        # NOTE: This can be more efficient, but I'm focusing on lower-code for now
        return {k: v for k, v in self.__fields__.items() if k not in self.__arbitrary_fields__}
