"""Global pytest settings."""

from pathlib import Path
from uuid import uuid4

import pytest
from pytest_lazyfixture import lazy_fixture

from pydantic_cereal import Cereal


@pytest.fixture
def random_path() -> str:
    """Generate a random path."""
    return str(uuid4()).replace("-", "")


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


@pytest.fixture(params=[lazy_fixture("uri_memory"), lazy_fixture("uri_localdir")])
def uri(request: pytest.FixtureRequest) -> str:
    """Fixture for URI for different filesystems."""
    return str(request.param)


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
