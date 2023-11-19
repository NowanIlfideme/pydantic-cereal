"""Pandas example."""

import pandas as pd


def pd_write(obj: pd.DataFrame, uri: str) -> None:
    """Write Pandas dataframe to URI."""
    obj.to_parquet(uri)


def pd_read(uri: str) -> pd.DataFrame:
    """Read Pandas dataframe from URI."""
    return pd.read_parquet(uri)
