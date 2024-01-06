"""Define types with pandas."""
"""Test Pandas models."""

# ruff: noqa: E402
import pytest

pytest.importorskip("pandas")

import pandas as pd
from pydantic import BaseModel, ConfigDict

from pydantic_cereal.examples.ex_pd import pd_read, pd_write

from .common import cereal

PandasDF = cereal.wrap_type(pd.DataFrame, reader=pd_read, writer=pd_write)


class ModelWithPandas(BaseModel):
    """Foo class."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    pdf: PandasDF

    def __eq__(self, rhs: object) -> bool:
        """Check if objects are equal (since Pandas dataframes don't support `==`)."""
        if isinstance(rhs, ModelWithPandas):
            return self.pdf.equals(rhs.pdf)
        return NotImplemented
