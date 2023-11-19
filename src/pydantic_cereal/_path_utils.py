"""Universal path utilities."""

from os import PathLike
from typing import Union

from upath import UPath


def ensure_empty_dir(uri: Union[str, PathLike, UPath]) -> UPath:
    """Ensure the directory exists, but is empty."""
    res = UPath(uri)
    try:
        next(res.rglob("*"))
    except StopIteration:
        pass
    else:
        raise FileExistsError(f"Non-empty directory exists at {uri!r}")
    res.mkdir(parents=True, exist_ok=True)
    return res
