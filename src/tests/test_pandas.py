"""Test Pandas models."""

# ruff: noqa: E402

import pytest
from pytest_lazyfixture import lazy_fixture

pytest.importorskip("pandas")

import pandas as pd
from fsspec import AbstractFileSystem
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


@pytest.mark.parametrize(
    "fs, target_path",
    [
        (lazy_fixture("fs_localdir"), lazy_fixture("random_path_in_localdir")),
        (lazy_fixture("fs_memory"), lazy_fixture("random_path")),
        (None, lazy_fixture("uri_localdir")),
        (None, lazy_fixture("uri_memory")),
    ],
)
def test_pandas_minimal(df: pd.DataFrame, fs: AbstractFileSystem, target_path: str):
    """Minimal test for pandas."""
    mdl = ModelWithPandas(pdf=df)

    cereal.write_model(mdl, target_path, fs)
    mdl_rt = cereal.read_model(target_path, fs)
    assert isinstance(mdl_rt, ModelWithPandas)
    assert mdl_rt.pdf.equals(df)
