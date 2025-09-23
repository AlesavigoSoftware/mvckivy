from __future__ import annotations

import logging
import os
import sys
from fnmatch import fnmatch
from importlib import reload
from os.path import realpath
from pathlib import Path
from typing import Iterable

from kivy.base import ExceptionHandler
from kivy.clock import mainthread, Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
)
from kivymd.utils.fpsmonitor import FpsMonitor

from mvckivy.app import MVCApp
from mvckivy.app.app import MKVApp
from mvckivy.project_management import PathItem
from mvckivy.utils.error_handlers import ClockHandler, AppExceptionNotifyHandler
from mvckivy.utils.hot_reload_utils import HotReloadConfig, EXCEPTION_POPUP_KV


original_argv = sys.argv
logger = logging.getLogger("mvckivy")


class MKVDebugApp(MKVApp):
    debug_mode = BooleanProperty(True)
    raise_error = BooleanProperty(not debug_mode.defaultvalue)
    """
    When the `debug_mode` is activated, 
    it will show any error on the screen instead of raising it.
    """
    show_fps_monitor = BooleanProperty(True)
    manual_reload_key_code = NumericProperty(32)  # Space key
    foreground_lock = BooleanProperty(False)
    hotreload_config: HotReloadConfig | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._observer = None
        self.w_handler = None

    @classmethod
    def get_exception_handlers(cls) -> list[ExceptionHandler]:
        return [ClockHandler(), AppExceptionNotifyHandler()]

    @mainthread
    def set_error(self, exc, tb=None):
        if self.debug_mode:
            popup = Builder.load_string(EXCEPTION_POPUP_KV)
            popup.text = f"{exc}\n\n{tb or ''}"
            popup.open()

    def build(self):
        if not self.debug_mode:
            return super().build()

        self.hotreload_config = self.fill_hotreload_config(HotReloadConfig())

        if self.show_fps_monitor:
            self.fps_monitor_start()

        if self.foreground_lock:
            self.prepare_foreground_lock()

        self.patch_builder()
        self.enable_manual_reload()
        self.enable_autoreload()

        self.rebuild(first=True)

        return super().build()

    def fill_hotreload_config(
        self, hotreload_config: HotReloadConfig
    ) -> HotReloadConfig:
        raise NotImplementedError()

    @staticmethod
    def fps_monitor_start(anchor: str = "top") -> None:
        """
        Adds a monitor to the main application window.

        :type anchor: str;
        :param anchor: anchor FPS panel ('top' or 'bottom');
        """

        def add_monitor(*args):
            monitor = FpsMonitor(anchor=anchor)
            monitor.start()
            Window.add_widget(monitor)

        Clock.schedule_once(add_monitor)

    def prepare_foreground_lock(self):
        """
        Try forcing app to front permanently to avoid windows
        pop-ups and notifications etc.app.

        Requires fake full screen and borderless.

        .. note::
            This function is called automatically if `FOREGROUND_LOCK` is set
        """

        try:
            import ctypes

            LSFW_LOCK = 1
            ctypes.windll.user32.LockSetForegroundWindow(LSFW_LOCK)
            logger.info("%s: Foreground lock activated", self.appname)
        except Exception:
            logger.warning("%s: No foreground lock available", self.appname)

    def patch_builder(self):
        Builder.orig_load_string = Builder.load_string
        Builder.load_string = self._builder_load_string

    def _builder_load_string(self, string, **kwargs):
        if "filename" not in kwargs:
            from inspect import getframeinfo, stack

            caller = getframeinfo(stack()[1][0])
            kwargs["filename"] = caller.filename
        return Builder.orig_load_string(string, **kwargs)

    def enable_manual_reload(self):
        """
        Enable manual reload by key press.
        Default key is space.
        """

        key_names = {
            32: "Space [default]",
            13: "Enter",
            9: "Tab",
            103: "F4",
            102: "F3",
            101: "F2",
            100: "F1",
            105: "F6",
            104: "F5",
            108: "F10",
            107: "F9",
            106: "F8",
            109: "F11",
            110: "F12",
        }
        logger.info(
            "%s: Manual reload activated, keycode: %d - %s",
            self.appname,
            self.manual_reload_key_code,
            key_names.get(
                self.manual_reload_key_code, f"Unknown-{self.manual_reload_key_code}"
            ),
        )
        Window.bind(
            on_keyboard=lambda window, keycode, *args: (
                self.rebuild() if self.manual_reload_key_code == keycode else None
            )
        )

    def enable_autoreload(self):
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.error("%s: Auto reloader is missing watchdog", self.appname)
            return
        logger.info("%s: Auto reloader activated", self.appname)
        self.w_handler = handler = FileSystemEventHandler()
        handler.dispatch = self._reload_from_watchdog
        self._observer = observer = Observer()
        for path in self.hotreload_config.autoreloader_paths:
            options = {"recursive": True}
            if isinstance(path, Iterable):
                path, options = path
            observer.schedule(handler, path, **options)
        observer.start()

    @mainthread
    def _reload_from_watchdog(self, event):
        from watchdog.events import FileModifiedEvent

        if not isinstance(event, FileModifiedEvent):
            return

        for pat in self.hotreload_config.autoreloader_ignore_patterns:
            if fnmatch(event.src_path, pat):
                return

        if event.src_path.endswith(".py"):
            Builder.unload_file(event.src_path)
            self._reload_py(event.src_path)

        Clock.unschedule(self.rebuild)
        Clock.schedule_once(self.rebuild, 0.05)

    def _reload_py(self, filename):
        # We don't have dependency graph yet, so if the module actually exists
        # reload it.

        filename = PathItem(realpath(filename))
        # Check if it's our own application file.
        try:
            mod = sys.modules[self.__class__.__module__]
            mod_filename = realpath(mod.__file__)
        except Exception:
            mod = None
            mod_filename = None

        # Detect if it's the application class // main.
        if mod_filename == filename.str():
            return self._restart_app(mod)

        module = self._filename_to_module(filename)
        if module in sys.modules:
            logger.debug("{}: Module exist, reload it".format(self.appname))
            Factory.unregister_from_filename(filename)
            self._unregister_factory_from_module(module)
            reload(sys.modules[module])

    def _restart_app(self, mod, os=None):
        _has_execv = sys.platform != "win32"
        cmd = [sys.executable] + original_argv
        if not _has_execv:
            import subprocess

            subprocess.Popen(cmd)
            sys.exit(0)
        else:
            try:
                os.execv(sys.executable, cmd)
            except OSError:
                os.spawnv(os.P_NOWAIT, sys.executable, cmd)
            finally:
                os._exit(0)

    def _filename_to_module(self, filename: PathItem):
        """Translate a file path to a Python module name in a
        platform‑independent way.

        Strategy:
        1) If the file is already imported, pick its module name from
           ``sys.modules`` by matching ``__file__``.
        2) Else, compute a dotted path relative to the project root from
           ``get_root_path``. If that fails (file outside project), try to
           make it relative to any entry in ``sys.path``.
        3) Normalize ``__init__.py`` to the package name (drop the filename).
        """

        # Normalize to Path (accept PathItem/str/Path)
        p = filename.path() if isinstance(filename, PathItem) else Path(filename)
        try:
            file_real = p.resolve()
        except Exception:
            file_real = Path(realpath(str(p)))

        # 1) Try to find an already-loaded module with matching __file__
        module_name = None
        for name, mod in list(sys.modules.items()):
            try:
                mod_file = getattr(mod, "__file__", None)
                if not mod_file:
                    continue
                if Path(mod_file).resolve() == file_real:
                    module_name = name
                    break
            except Exception:
                continue

        def to_module_from_relative(rel_path: Path) -> str:
            # Drop extension and convert to dotted path. Handle __init__.py
            if rel_path.name == "__init__.py":
                rel_path = rel_path.parent
            else:
                rel_path = rel_path.with_suffix("")
            parts = [part for part in rel_path.parts if part not in ("", os.sep)]
            return ".".join(parts)

        if module_name is None:
            # 2a) Try relative to project root
            try:
                root = self.get_root_path().path().resolve()
            except Exception:
                root = Path.cwd().resolve()

            try:
                rel = file_real.relative_to(root)
                module_name = to_module_from_relative(rel)
            except Exception:
                # 2b) Try to make path relative to any sys.path entry
                for entry in map(Path, sys.path):
                    try:
                        base = entry.resolve()
                    except Exception:
                        continue
                    try:
                        rel = file_real.relative_to(base)
                        module_name = to_module_from_relative(rel)
                        break
                    except Exception:
                        continue

        if module_name is None:
            # 2c) Last-resort: build from absolute path without the anchor
            rel = file_real.with_suffix("")
            parts = list(rel.parts)
            # remove anchor like 'C:\\' or '/' if present
            if parts and (Path(parts[0]).anchor == parts[0] or parts[0] in ("/", "\\")):
                parts = parts[1:]
            module_name = ".".join(parts)

        logger.debug(
            "{}: Translated {} to {}".format(self.appname, str(filename), module_name)
        )
        return module_name

    def _unregister_factory_from_module(self, module):
        # Check module directly.
        to_remove = [
            x for x in Factory.classes if Factory.classes[x]["module"] == module
        ]
        # Check class name.
        for x in Factory.classes:
            cls = Factory.classes[x]["cls"]
            if not cls:
                continue
            if getattr(cls, "__module__", None) == module:
                to_remove.append(x)

        for name in set(to_remove):
            del Factory.classes[name]

    def rebuild(self, *args, first=False, **kwargs):
        if not first:
            logger.info("%s: Rebuilding the application", self.appname)
            self.unload_app_dependencies()
            Builder.rulectx = {}
            self.load_app_dependencies()
            self.root.screen_manager.clear_widgets()

        self.fill_root(first=first)

    def unload_app_dependencies(self):
        """
        Called when all the application dependencies must be unloaded.
        Usually happen before a reload
        """

        for path_to_kv_file in self.hotreload_config.kv_files:
            path_to_kv_file = realpath(path_to_kv_file)
            Builder.unload_file(path_to_kv_file)

        for name, module in self.hotreload_config.classes.items():
            Factory.unregister(name)

        for path in self.hotreload_config.kv_dirs:
            for path_to_dir, dirs, files in os.walk(path):
                for name_file in files:
                    if os.path.splitext(name_file)[1] == ".kv":
                        path_to_kv_file = os.path.join(path_to_dir, name_file)
                        Builder.unload_file(path_to_kv_file)

    def load_app_dependencies(self):
        """
        Load all the application dependencies.
        This is called before rebuild.
        """

        for path_to_kv_file in self.hotreload_config.kv_files:
            path_to_kv_file = realpath(path_to_kv_file)
            Builder.load_file(path_to_kv_file)

        for name, module in self.hotreload_config.classes.items():
            Factory.register(name, module=module)

        for path in self.hotreload_config.kv_dirs:
            for path_to_dir, dirs, files in os.walk(path):
                for name_file in files:
                    if os.path.splitext(name_file)[1] == ".kv":
                        path_to_kv_file = os.path.join(path_to_dir, name_file)
                        Builder.load_file(path_to_kv_file)


class MVCDebugApp(MKVDebugApp, MVCApp):
    def fill_root(self, first: bool) -> None:
        if first:
            for spec in self.hotreload_config.screens:
                self.create_screen(
                    spec["name"], create_children=spec["recreate_children"]
                )
        else:
            for spec in self.hotreload_config.screens:
                self.recreate_screen(
                    spec["name"], recreate_children=spec["recreate_children"]
                )
