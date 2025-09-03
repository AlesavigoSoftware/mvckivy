from __future__ import annotations

from pathlib import Path
from typing import Union


class PathItem:
    def __init__(self, path: Union[str, Path, PathItem]):
        self._path: Path = path.path() if isinstance(path, PathItem) else Path(path)

    def __str__(self) -> str:
        return str(self._path)

    def str(self) -> str:
        return str(self._path)

    def path(self) -> Path:
        return self._path

    def join(self, *args: Union[str, Path, PathItem]) -> PathItem:
        args = [arg.path() if isinstance(arg, PathItem) else Path(arg) for arg in args]
        new_path = self._path.joinpath(*args)
        return PathItem(new_path)

    def exists(self) -> bool:
        return self._path.exists()


class MVCPathManager:
    """
    Instance-based path manager for an MVC app.

    Provide the project root at construction time. All other directories are
    derived as properties relative to that root, preserving the original
    folder structure names.
    """

    def __init__(self, proj_root: Union[str, Path, PathItem]):
        self._proj_dir: PathItem = (
            proj_root if isinstance(proj_root, PathItem) else PathItem(proj_root)
        )

    @classmethod
    def join_paths(cls, *args: Union[Path, str, PathItem]) -> PathItem:
        args = [arg.path() if isinstance(arg, PathItem) else Path(arg) for arg in args]
        return PathItem(Path().joinpath(*args))

    @property
    def proj_dir(self) -> PathItem:
        return self._proj_dir

    @property
    def views_dir(self) -> PathItem:
        return self._proj_dir.join("views")

    @property
    def models_dir(self) -> PathItem:
        return self._proj_dir.join("models")

    @property
    def controllers_dir(self) -> PathItem:
        return self._proj_dir.join("controllers")

    @property
    def logs_dir(self) -> PathItem:
        return self._proj_dir.join("logs")

    @property
    def cache_dir(self) -> PathItem:
        return self._proj_dir.join("cache")
