"""Pandas example."""

import pandas as pd
from fsspec import AbstractFileSystem


def pd_write(obj: pd.DataFrame, fs: AbstractFileSystem, path: str) -> None:
    """Write Pandas dataframe (as Parquet) to a path within a filesystem."""
    with fs.open(path, mode="wb") as f:
        obj.to_parquet(f)  # type: ignore


def pd_read(fs: AbstractFileSystem, path: str) -> pd.DataFrame:
    """Read Pandas dataframe (as Parquet) from a path within a filesystem."""
    with fs.open(path, mode="rb") as f:
        obj = pd.read_parquet(f)  # type: ignore
    return obj
