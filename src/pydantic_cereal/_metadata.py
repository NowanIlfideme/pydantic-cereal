from pydantic import BaseModel

from .version import __version__

ImportString = str


class CerealInfo(BaseModel):
    """Main information of serialization."""

    cereal_version: str = __version__
    cereal_writer: ImportString
    cereal_reader: ImportString
    object_path: str


cereal_meta_schema = CerealInfo.model_json_schema()
"""Metadata schema for pydantic-cereal metadata."""
