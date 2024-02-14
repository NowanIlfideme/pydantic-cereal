"""Polars example."""

import polars as pl
from fsspec import AbstractFileSystem


def pl_write(obj: pl.DataFrame, fs: AbstractFileSystem, path: str) -> None:
    """Write Pandas dataframe (as Parquet) to a path within a filesystem."""
    with fs.open(path, mode="wb") as f:
        obj.write_parquet(f)


def pl_read(fs: AbstractFileSystem, path: str) -> pl.DataFrame:
    """Read Pandas dataframe (as Parquet) from a path within a filesystem."""
    with fs.open(path, mode="rb") as f:
        # NOTE: There is some collision happening with polars when passing 'f' directly
        obj = pl.read_parquet(f.read())
    return obj
