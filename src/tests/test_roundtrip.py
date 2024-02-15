"""Test round-tripping of custom objects in many different file systems."""

from pathlib import Path
from typing import Callable, Tuple

import pytest
from fsspec import AbstractFileSystem
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from fsspec.implementations.zip import ZipFileSystem
from pydantic import BaseModel
from pytest_cases import parametrize_with_cases

from .common import cereal

MakeFS = Callable[[], AbstractFileSystem]  # function that makes a file system


class FileSystemTestCases:
    """File systems for testing."""

    def case_memory_fs(self) -> Tuple[MakeFS, MakeFS]:
        """Memory file system."""
        fs = MemoryFileSystem()
        return lambda: fs, lambda: fs

    def case_local_fs(self, tmp_path: Path) -> Tuple[MakeFS, MakeFS]:
        """Local file system, mounted to a known-safe temporary path."""
        fs = DirFileSystem(path=str(tmp_path.resolve()), fs=LocalFileSystem())
        return lambda: fs, lambda: fs

    def case_gcs_fs(self) -> Tuple[MakeFS, MakeFS]:
        """Google Cloud Storage file system."""
        try:
            import gcsfs

            gcs_project = "pydantic-cereal"
            gcs_bucket = "pydantic-cereal-testing"
            token_path = Path("secrets/gcloud_key.json")
            if token_path.exists():
                token = str(token_path)
            else:
                token = None

            raw_fs = gcsfs.GCSFileSystem(project=gcs_project, token=token)
            raw_fs.ls(gcs_bucket)  # check if bucket is available
            fs = DirFileSystem(path=gcs_bucket, fs=raw_fs)
            return lambda: fs, lambda: fs
        except Exception:
            pytest.skip("Google Cloud Storage not set up.")

    def case_zip_in_local_fs(self, tmp_path: Path) -> Tuple[MakeFS, MakeFS]:
        """Zip file system on disk."""
        zip_path = tmp_path / "zipfile.zip"

        return lambda: ZipFileSystem(
            f"file://{zip_path.resolve()}", mode="w", allowZip64=True
        ), lambda: ZipFileSystem(f"file://{zip_path.resolve()}", mode="r", allowZip64=True)


class CerealObjectTestCases:
    """Test cases of Cereal objects."""

    def case_my_model(self) -> BaseModel:
        """Case for my model."""
        from .def_mytype import MyModel, MyType

        return MyModel(fld=MyType("my_field"))

    def case_pandas_model(self) -> BaseModel:
        """Case with a Pandas model installed."""
        from .def_pandas import ModelWithPandas, pd

        df = pd.DataFrame({"foo": [1, 2, 3]})
        mdl = ModelWithPandas(pdf=df)
        return mdl

    def case_polars_model(self) -> BaseModel:
        """Case with a Polars model installed."""
        from .def_polars import ModelWithPolars, pl

        df = pl.DataFrame({"foo": [1, 2, 3]})
        mdl = ModelWithPolars(pldf=df)
        return mdl


@parametrize_with_cases(["fs_write", "fs_read"], cases=FileSystemTestCases)
@parametrize_with_cases(["obj"], cases=CerealObjectTestCases)
def test_roundtrip_fs(fs_write: MakeFS, fs_read: MakeFS, obj: BaseModel, random_path: str):
    """Test round-tripping of objects given different filesystems."""
    path = random_path
    fs1 = fs_write()
    # with fs1.open("foo", mode="w") as f1:
    #     f1.write("foo bar")
    cereal.write_model(obj, path, fs=fs1)
    del fs1  # HACK: This is used to close any zip files... not great

    fs2 = fs_read()
    # with fs2.open("foo", mode="r") as f2:
    #     x = f2.read()
    obj2 = cereal.read_model(path, fs=fs2)
    assert obj2 == obj


class UriTestCases:
    """Test cases for URIs."""

    def case_memory_uri(self) -> str:
        """Memory URI."""
        return "memory://path"

    def case_local_uri(self, tmp_path: Path) -> str:
        """Local path URI."""
        return f"file://{tmp_path.resolve()}"


@parametrize_with_cases(["uri"], cases=UriTestCases)
@parametrize_with_cases(["obj"], cases=CerealObjectTestCases)
def test_roundtrip_uri(uri: str, obj: BaseModel, random_path: str):
    """Test round-tripping of objects given different URIs."""
    path = random_path

    cereal.write_model(obj, f"{uri}/{path}")

    obj2 = cereal.read_model(f"{uri}/{path}")
    assert obj2 == obj
