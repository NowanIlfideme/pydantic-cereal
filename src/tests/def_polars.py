"""Define types with polars, to be used for testing."""

# ruff: noqa: E402
import polars as pl
from pydantic import BaseModel, ConfigDict

from pydantic_cereal.examples.ex_pl import pl_read, pl_write

from .common import cereal

PolarsDF = cereal.wrap_type(pl.DataFrame, pl_read, pl_write)


class ModelWithPolars(BaseModel):
    """Foo class."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    pldf: PolarsDF

    def __eq__(self, rhs: object) -> bool:
        """Check if objects are equal (since Polars dataframes don't support `==`)."""
        if isinstance(rhs, ModelWithPolars):
            return self.pldf.equals(rhs.pldf)
        return NotImplemented
