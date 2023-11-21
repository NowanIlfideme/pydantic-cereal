"""Global settings."""

import pytest

from pydantic_cereal import Cereal


@pytest.fixture
def cereal() -> Cereal:
    """Global cereal object, used as a fixture."""
    return Cereal()
