from __future__ import annotations

from pathlib import Path

import pytest

from mvckivy.app.screens_schema import AppSchema
from mvckivy.project_management import PathItem


# Dummy types to avoid importing kivy-dependent classes
class DummyModel:  # noqa: D401 - simple stub
    """Stub model class for schema typing."""


class DummyController:  # noqa: D401 - simple stub
    """Stub controller class for schema typing."""


class DummyScreen:  # noqa: D401 - simple stub
    """Stub screen class for schema typing."""


class BaseTestSchema(AppSchema):
    @classmethod
    def make_entry(
        cls,
        name: str,
        *,
        children: list[str] | None = None,
        parent: str | None = None,
        kv_path: str | Path | PathItem | None | object = ...,
    ):
        entry = {
            "name": name,
            "model_cls": DummyModel,
            "controller_cls": DummyController,
            "screen_cls": DummyScreen,
            "children": children or [],
        }
        if parent is not None:
            entry["parent"] = parent
        if kv_path is not ...:  # explicitly provided by caller
            entry["kv_path"] = kv_path  # can be None, Path-like, or PathItem
        return entry


def install_fake_kivy_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Install a minimal fake `kivy.app.App` into sys.modules so that
    `App.get_running_app()` returns an object exposing `path_manager.proj_dir`.
    """
    import types, sys

    class _PM:
        def __init__(self, proj_dir: Path):
            self.proj_dir = PathItem(proj_dir)

    class _App:
        path_manager = _PM(tmp_path)

    kivy_pkg = types.ModuleType("kivy")
    kivy_app_mod = types.ModuleType("kivy.app")

    class App:
        @staticmethod
        def get_running_app():
            return _App

    kivy_app_mod.App = App
    monkeypatch.setitem(sys.modules, "kivy", kivy_pkg)
    monkeypatch.setitem(sys.modules, "kivy.app", kivy_app_mod)


def test_auto_fill_kv_path_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install_fake_kivy_app(tmp_path, monkeypatch)

    # Create default folders for root and child
    views = tmp_path / "views"
    (views / "app_screen").mkdir(parents=True)
    (views / "app_screen" / "children" / "initial_screen").mkdir(parents=True)

    class Schema(BaseTestSchema):
        @classmethod
        def create_schema(cls):
            return [
                cls.make_entry("app_screen", children=["initial_screen"]),
                cls.make_entry("initial_screen", parent="app_screen"),
            ]

    schema = Schema.get_schema(recreate=True)
    by_name = {e["name"]: e for e in schema}
    assert isinstance(by_name["app_screen"]["kv_path"], PathItem)
    assert isinstance(by_name["initial_screen"]["kv_path"], PathItem)
    assert by_name["app_screen"]["kv_path"].path() == views / "app_screen"
    assert (
        by_name["initial_screen"]["kv_path"].path()
        == views / "app_screen" / "children" / "initial_screen"
    )


def test_keep_none_when_explicit_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install_fake_kivy_app(tmp_path, monkeypatch)

    # Only create root folder so child can fall back to None cleanly
    (tmp_path / "views" / "app_screen").mkdir(parents=True)

    class Schema(BaseTestSchema):
        @classmethod
        def create_schema(cls):
            return [
                cls.make_entry("app_screen", children=["initial_screen"]),
                cls.make_entry("initial_screen", parent="app_screen", kv_path=None),
            ]

    schema = Schema.get_schema(recreate=True)
    by_name = {e["name"]: e for e in schema}
    assert isinstance(by_name["app_screen"]["kv_path"], PathItem)
    assert by_name["initial_screen"]["kv_path"] is None


def test_validate_explicit_kv_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install_fake_kivy_app(tmp_path, monkeypatch)

    # Create custom path for child
    custom = tmp_path / "custom_child"
    custom.mkdir(parents=True)

    # Root default path must exist
    (tmp_path / "views" / "app_screen").mkdir(parents=True)

    class Schema(BaseTestSchema):
        @classmethod
        def create_schema(cls):
            return [
                cls.make_entry("app_screen", children=["initial_screen"]),
                cls.make_entry("initial_screen", parent="app_screen", kv_path=custom),
            ]

    schema = Schema.get_schema(recreate=True)
    by_name = {e["name"]: e for e in schema}
    assert by_name["initial_screen"]["kv_path"].path() == custom


def test_fail_when_default_dir_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install_fake_kivy_app(tmp_path, monkeypatch)
    # Intentionally do NOT create app_screen folder

    class Schema(BaseTestSchema):
        @classmethod
        def create_schema(cls):
            return [
                cls.make_entry("app_screen", children=["initial_screen"]),
                cls.make_entry("initial_screen", parent="app_screen"),
            ]

    with pytest.raises(FileNotFoundError):
        Schema.get_schema(recreate=True)


def test_fail_when_explicit_path_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    install_fake_kivy_app(tmp_path, monkeypatch)

    # Root default exists, child explicit points to missing dir
    (tmp_path / "views" / "app_screen").mkdir(parents=True)
    missing = tmp_path / "missing_child"

    class Schema(BaseTestSchema):
        @classmethod
        def create_schema(cls):
            return [
                cls.make_entry("app_screen", children=["initial_screen"]),
                cls.make_entry("initial_screen", parent="app_screen", kv_path=missing),
            ]

    with pytest.raises(FileNotFoundError):
        Schema.get_schema(recreate=True)
