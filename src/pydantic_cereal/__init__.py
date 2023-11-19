"""Advanced serialization for Pydantic models."""

__all__ = ["Cereal", "cereal_meta_schema", "__version__"]

from .main import Cereal, cereal_meta_schema
from .version import __version__
