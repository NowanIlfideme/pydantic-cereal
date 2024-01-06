"""Global pytest settings."""

from uuid import uuid4

import pytest


@pytest.fixture
def random_path() -> str:
    """Generate a random path."""
    return str(uuid4()).replace("-", "")
