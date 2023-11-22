"""Test Pandas models."""

# ruff: noqa: E402

import pytest

pytest.importorskip("pandas")

import pandas as pd
from pydantic import BaseModel, ConfigDict

from pydantic_cereal import Cereal
from pydantic_cereal.examples.ex_pd import pd_read, pd_write

cereal = Cereal()
PandasDF = cereal.wrap_type(pd.DataFrame, reader=pd_read, writer=pd_write)


class ModelWithPandas(BaseModel):
    """Foo class."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    pdf: PandasDF


@pytest.fixture
def df() -> pd.DataFrame:
    """Create pandas dataframe for testing."""
    return pd.DataFrame({"foo": [1, 2, 3]})


def test_pandas_minimal(df: pd.DataFrame, uri: str):
    """Minimal test for pandas."""
    mdl = ModelWithPandas(pdf=df)
    cereal.write_model(mdl, uri)
    mdl_rt = cereal.read_model(uri)
    assert isinstance(mdl_rt, ModelWithPandas)
    assert mdl_rt.pdf.equals(df)
