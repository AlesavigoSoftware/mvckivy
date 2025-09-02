from __future__ import annotations

from pathlib import Path
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mvckivy.app import ScreensSchema


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
    proj_dir = PathItem(Path(__file__).parents[1])

    @classmethod
    def join_paths(cls, *args: Union[Path, str, PathItem]) -> PathItem:
        args = [arg.path() if isinstance(arg, PathItem) else Path(arg) for arg in args]
        return PathItem(Path().joinpath(*args))


class MVCAppPathManager(MVCPathManager):
    proj_dir = PathItem(Path(__file__).parents[1])
    views_dir = PathItem(proj_dir.join("views"))
    models_dir = PathItem(proj_dir.join("models"))
    controllers_dir = PathItem(proj_dir.join("controllers"))
    logs_dir = PathItem(proj_dir.join("logs"))
    cache_dir = PathItem(proj_dir.join("cache"))
    screen_dirs: dict[str, PathItem] = {}

    @classmethod
    def register_screen_dirs(cls, schemas: list[ScreensSchema]) -> dict[str, PathItem]:
        cls.screen_dirs.clear()

        schema_by_name = {s["name"]: s for s in schemas}

        def resolve_path(name: str) -> PathItem:
            if name in cls.screen_dirs:
                return cls.screen_dirs[name]

            # If kv_path is specified, use it directly
            path_item: PathItem = schema_by_name[name]["kv_path"]
            if path_item:
                cls.register_screen_dir(name, path_item)
                return path_item

            parent: str | None = schema_by_name[name]["parent"]
            if parent:
                # parent path goes first
                parent_path = resolve_path(parent)
                path_item = parent_path.join("children", name)
            else:
                # root screen goes directly to views/<screen_name>
                path_item = cls.views_dir.join(name)

            cls.register_screen_dir(name, path_item)
            return path_item

        for screen_name in schema_by_name:
            resolve_path(screen_name)

        return cls.screen_dirs

    @classmethod
    def register_screen_dir(
        cls, screen_name: str, path: Union[str, Path, PathItem]
    ) -> None:
        p = PathItem(path)

        if not p.path().exists():
            raise FileNotFoundError(
                f"Directory for screen '{screen_name}' not found: {p}"
            )

        cls.screen_dirs[screen_name] = p
