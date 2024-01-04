"""Global pytest settings."""

import zipfile
from pathlib import Path
from uuid import uuid4

import fsspec
import pytest
from fsspec import get_fs_token_paths
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from fsspec.implementations.zip import ZipFileSystem
from pytest_lazyfixture import lazy_fixture

from pydantic_cereal import Cereal


@pytest.fixture
def random_path() -> str:
    """Generate a random path."""
    return str(uuid4()).replace("-", "")


@pytest.fixture
def random_path_in_localdir(tmp_path: str, random_path: str) -> str:
    """Get path to a randomly generated directory in temporary directory."""
    return f"{tmp_path}/{random_path}"


@pytest.fixture
def uri_memory(random_path: str) -> str:
    """Create MemoryFileSystem URI.

    NOTE: MemoryFileSystem root is not `"/"` but rather `""`.
    """
    return f"memory://{random_path}"


@pytest.fixture
def uri_localdir(tmp_path: Path, random_path: str) -> str:
    """Create LocalFileSystem URI."""
    # For some reason, this doesn't work: f"file://{tmp_path!s}/{random_path!s}"
    # It returns `LocalPath` but it should be a PosixPath - bug in `universal_pathlib` I guess?
    # TODO: Report bug, and reconsider using `universal_pathlib` in gereral? Or help fix the bugs :)
    return f"{tmp_path!s}/{random_path!s}"


@pytest.fixture
def uri_zip_in_localdir(random_path: str, random_path_in_localdir: str):
    """URI to zip in a temporary local directory."""
    with fsspec.open(f"file://{random_path_in_localdir}/{random_path}.zip", "wb") as zip_file:
        with zipfile.ZipFile(zip_file, "w") as _:
            pass
    return f"zip://::file://{random_path_in_localdir!s}/{random_path}"


@pytest.fixture
def uri_zip_in_memory(random_path: str):
    """URI to zip in memory."""
    with fsspec.open(f"memory://{random_path}.zip", "wb") as zip_file:
        with zipfile.ZipFile(zip_file, "w") as _:
            pass
    return f"zip://::memory://{random_path}"


@pytest.fixture(params=[lazy_fixture("uri_memory"), lazy_fixture("uri_localdir")])
def uri(request: pytest.FixtureRequest) -> str:
    """Fixture for URI for different filesystems."""
    return str(request.param)


@pytest.fixture
def fs_memory() -> MemoryFileSystem:
    """MemoryFileSystem at root of memory."""
    fs, _, _ = get_fs_token_paths("memory://")
    return fs


@pytest.fixture
def fs_localdir() -> LocalFileSystem:
    """LocalFileSystem in temporary directory."""
    fs, _, _ = get_fs_token_paths("file://")
    return fs


@pytest.fixture
def fs_zip_in_memory(random_path: str, fs_memory: MemoryFileSystem) -> ZipFileSystem:
    """ZipFileSystem to zipfile in memory."""
    with fs_memory.open(f"{random_path}.zip", "wb") as zip_file:
        with zipfile.ZipFile(zip_file, "w") as _:
            pass
    # ZipFS can only be either "r" or "w"
    fs_zip = ZipFileSystem(fo=f"memory://{random_path}.zip", mode="w")
    return fs_zip


@pytest.fixture
def fs_zip_in_localdir(tmp_path: Path, random_path: str, fs_localdir: LocalFileSystem) -> ZipFileSystem:
    """ZipFileSystem to zipfile in temporary directory."""
    with fs_localdir.open(f"{tmp_path!s}/{random_path}.zip", "wb") as zip_file:
        with zipfile.ZipFile(zip_file, "w") as _:
            pass
    # ZipFS can only be either "r" or "w"
    fs_zip = ZipFileSystem(fo=f"file://{tmp_path!s}/{random_path}.zip", mode="w")
    return fs_zip


@pytest.fixture
def cereal() -> Cereal:
    """Global cereal object, if used as a fixture.

    Note
    ----
    This fixture is likely not that useful.

    You can't create a Pydantic model inside a function, because we can't import locals.
    Instead, define it in a top-level module, then import it.
    To define the model, you need to have the proper field types already added...


    """
    return Cereal()
