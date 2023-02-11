"""Wrappers for Pydantic v1.X compatibility."""

if True:
    import pydantic

    assert pydantic.__version__ < "2"

from inspect import isabstract
from typing import TYPE_CHECKING, Any

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


def get_pydantic_arbitrary_fields(model: type[BaseModel]) -> dict[str, ModelField]:
    """Gets the 'arbitrary' fields from a Pydantic model."""
    return {name: fld for name, fld in model.__fields__.items() if is_pydantic_arbitrary_type(fld.type_)}


class CerealModel(BaseModel):
    """Pydantic model with advanced serialization enabled.

    This also changes some model config options.
    """

    if TYPE_CHECKING:
        __arbitrary_fields__: dict[str, ModelField]
        __pure_fields__: dict[str, ModelField]
        __pure_model__: type[BaseModel]

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
        if not isabstract(cls):
            # Select arbitrary and pure fields
            cls.__arbitrary_fields__ = get_pydantic_arbitrary_fields(cls)
            cls.__pure_fields__ = {
                k: v for k, v in cls.__fields__.items() if k not in cls.__arbitrary_fields__
            }

            # Create "pure" model version
            pure_kwargs: dict[str, Any] = {}
            for k, v in cls.__pure_fields__.items():
                if v.required:
                    if v.default:
                        pure_kwargs[k] = (v.type_, v.default)
                    else:
                        pure_kwargs[k] = (v.type_, ...)
                else:
                    pure_kwargs[k] = (v.type_, None)
            cls.__pure_model__ = pydantic.create_model(
                cls.__name__,
                __config__=cls.Config,
                __module__=cls.__module__,
                **pure_kwargs,
            )

    def _get_pure_model(self) -> BaseModel:
        """Creates a 'pure' Pydantic model of this type.

        Note that all validations are ignored.
        """
        return self.__pure_model__(**self.dict())
