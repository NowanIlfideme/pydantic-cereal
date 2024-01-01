"""Universal path utilities."""

from fsspec import AbstractFileSystem


def ensure_empty_dir(fs: AbstractFileSystem, workdir: str) -> str:
    """Ensure the directory exists, but is empty."""
    dir_contents = fs.listdir(workdir)
    if len(dir_contents) > 0:
        raise FileExistsError(f"Non-empty directory exists at {workdir!r}")
    return workdir


def append_filename(fs: AbstractFileSystem, path: str, filename: str) -> str:
    """Append filename to a path given filesystem."""
    return path + fs.sep + filename
