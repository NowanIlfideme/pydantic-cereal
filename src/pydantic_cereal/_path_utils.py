"""Universal path utilities."""

from fsspec import AbstractFileSystem


def ensure_empty_dir(fs: AbstractFileSystem, workdir: str) -> str:
    """Ensure the directory exists, but is empty."""
    if fs.exists(workdir):
        dir_contents = fs.listdir(workdir)
        if len(dir_contents) > 0:
            raise FileExistsError(f"Non-empty directory exists at {workdir!r}")
    else:
        fs.makedirs(workdir, exist_ok=True)
    return workdir


def append_path_parts(fs: AbstractFileSystem, path_base: str, *path_parts: str) -> str:
    """Append parts to a path given filesystem."""
    return str(fs.sep).join([path_base, *path_parts])
