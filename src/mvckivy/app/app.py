from __future__ import annotations

from fnmatch import fnmatch
from importlib import reload
import logging
import os
from os.path import realpath
from pathlib import Path
import sys
import trio
from trio import Nursery
from typing import TYPE_CHECKING, Iterable, Literal

from kivy.app import App
from kivy.base import ExceptionManager, ExceptionHandler, async_runTouchApp
from kivy.clock import mainthread, Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    ObjectProperty,
    StringProperty,
    BooleanProperty,
    NumericProperty,
)
from kivy.uix.widget import Widget

from kivymd.theming import ThemeManager
from kivymd.utils.fpsmonitor import FpsMonitor

from mvckivy.app import ScreenRegistrator
from mvckivy.project_management.path_manager import MVCPathManager
from mvckivy.utils.builder import MVCBuilder
from mvckivy.utils.constants import Scheme, Palette
from mvckivy.utils.error_handlers import ClockHandler, AppExceptionNotifyHandler
from mvckivy.utils.hot_reload_utils import HotReloadConfig, EXCEPTION_POPUP_KV


try:
    from monotonic import monotonic
except ImportError:
    monotonic = None


if TYPE_CHECKING:
    from mvckivy.base_mvc import BaseModel, BaseController, BaseScreen
    from mvckivy.base_mvc.base_app_controller import BaseAppController
    from mvckivy.base_mvc.base_app_model import BaseAppModel
    from mvckivy.base_mvc.base_app_screen import BaseAppScreen


original_argv = sys.argv
logger = logging.getLogger("mvckivy")


class MVCApp(App):
    __events__ = ["on_idle", "on_wakeup"]

    idle_detection = BooleanProperty(False)
    idle_timeout = NumericProperty(60)
    debug_mode: BooleanProperty = BooleanProperty(False)

    icon: StringProperty = StringProperty("kivymd/images/logo/kivymd-icon-512.png")
    theme_cls: ObjectProperty[ThemeManager] = ObjectProperty()

    model: ObjectProperty[BaseAppModel] = ObjectProperty()
    controller: ObjectProperty[BaseAppController] = ObjectProperty()
    screen: ObjectProperty[BaseAppScreen] = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nursery: Nursery | None = None
        self.idle_timer: monotonic = None
        self.path_manager = self.create_path_manager()
        self._registrator: ScreenRegistrator = self.create_screen_registrator()

        self.theme_cls: ThemeManager = ThemeManager()
        self.theme_cls.bind(
            theme_style=self.theme_cls.update_theme_colors,
            primary_palette=self.theme_cls.set_colors,
        )
        self.theme_cls.set_colors()

        if not self.config:
            self.load_config()  # AppModel contains ConfigParserProperties so utils must be loaded first

        MVCBuilder.load_libs_kv_files()
        self.load_all_screens_kv_files()

        self._registrator.create_models_and_controllers()
        self.model: BaseAppModel = self._registrator.get_app_model()
        self.controller: BaseAppController = self._registrator.get_app_controller()
        self.create_app_screen()
        self.screen: BaseAppScreen = self._registrator.get_app_screen()
        self.root = self.get_root()

        self._configure_window_behavior()
        self._configure_clock_behavior()
        self._register_error_handlers()

        self._bind_and_init_theme_settings()

    def log_screen_register_progress(self, load_info) -> None:
        """
        Log a single screen registration progress event.

        Accepts either a dict with keys ('name', 'current', 'total') or
        a ScreenRegistrationReport dataclass.
        """
        # Lazy import for typing-only dependency safety
        name = getattr(load_info, "name", "unknown")

        logger.debug(
            "mvckivy: Screen '%s' registered. Progress: %.2f%%",
            name,
            self._calc_screen_loading_progress(load_info, percent=True),
        )

    @staticmethod
    def _calc_screen_loading_progress(load_info, percent=False) -> float:
        current: float = getattr(load_info, "current", 1.0)
        total: float = getattr(load_info, "total", 1.0)
        res = round(current / total, 1)
        return res * 100.0 if percent else res

    @classmethod
    def get_exception_handlers(cls) -> list[ExceptionHandler]:
        return [
            ClockHandler(),
        ]

    def get_root(self) -> BaseAppScreen | None:
        """
        Get the root screen of the application.
        :return: Root screen instance.
        """
        return self._registrator.get_root()

    def get_model(self, name: str) -> BaseModel | None:
        """
        Get the model by its name.
        :param name: Name of the model.
        :return: Model instance.
        """
        return self._registrator.get_model(name)

    def get_controller(self, name: str) -> BaseController | None:
        """
        Get the controller by its name.
        :param name: Name of the controller.
        :return: Controller instance.
        """
        return self._registrator.get_controller(name)

    def get_screen(self, name: str) -> BaseScreen | None:
        """
        Get the screen by its name.
        :param name: Name of the screen.
        :return: Screen instance.
        """
        return self._registrator.get_screen(name)

    def get_models(self) -> Iterable[BaseModel] | None:
        return self._registrator.get_models()

    def get_controllers(self) -> Iterable[BaseController] | None:
        return self._registrator.get_controllers()

    def get_screens(self) -> Iterable[BaseScreen] | None:
        return self._registrator.get_screens()

    def get_root_path(self) -> Path:
        """
        Determines the absolute path to the module file where the concrete
        subclass of MVCApp is defined (accessible via `self.__class__`), then
        uses its parent directory as the project root for MVCPathManager.
        """
        try:
            module_name = self.__class__.__module__
            module = sys.modules.get(module_name)
            module_file = getattr(module, "__file__", None)
            if module_file:
                proj_root = Path(module_file).resolve().parent
            else:
                proj_root = Path.cwd().resolve()
        except Exception:
            proj_root = Path.cwd().resolve()

        return proj_root

    def create_path_manager(self) -> MVCPathManager:
        """
        Create a path manager rooted at the directory of the user's MVCApp subclass.
        """
        return MVCPathManager(self.get_root_path())

    def create_screen_registrator(self) -> ScreenRegistrator:
        raise NotImplementedError()

    # --- Adapters over ScreenRegistrator with built-in logging ---
    def _consume_and_log(self, generator: Iterable) -> None:
        for report in generator:
            self.log_screen_register_progress(report)

    def create_app_screen(self) -> None:
        self._consume_and_log(self._registrator.create_app_screen())

    def create_initial_screens(self) -> None:
        self._consume_and_log(self._registrator.create_initial_screens())

    def create_all_screens(self) -> None:
        self._consume_and_log(self._registrator.create_all_screens())

    def create_screen(self, name: str, *, create_children: bool = False) -> None:
        self._consume_and_log(
            self._registrator.create_screen(name, create_children=create_children)
        )

    def recreate_screen(self, name: str, *, recreate_children: bool = False) -> None:
        self._consume_and_log(
            self._registrator.recreate_screen(name, recreate_children=recreate_children)
        )

    def _bind_and_init_theme_settings(self) -> None:
        self.theme_cls.dynamic_color = True
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.3

        self.model.bind(theme_style=self.switch_theme)
        self.model.bind(primary_palette=self.switch_palette)
        self.model.bind(scheme_name=self.switch_scheme)

        self.switch_theme(None, self.model.theme_style)
        self.switch_palette(None, self.model.primary_palette)
        self.switch_scheme(None, self.model.scheme_name)

    def load_all_screens_kv_files(self) -> None:
        """
        Load all KV files from the screen directories.
        This method is called in the constructor of the application class.
        Children excluded from loading, as they are not part of the parent screen and load on them own separately.
        """
        for p in self._registrator.get_kv_paths().values():
            MVCBuilder.load_all_kv_files(p, directory_filters=["children"])

    def switch_theme(self, _, theme_style: Literal["Dark", "Light"]):
        self.theme_cls.theme_style = theme_style
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)  # Bugfix

    def switch_palette(
        self,
        _,
        primary_palette: Palette,
    ):
        self.theme_cls.primary_palette = primary_palette
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)  # Bugfix

    def switch_scheme(
        self,
        _,
        scheme_name: Scheme,
    ):
        self.theme_cls.dynamic_scheme_name = scheme_name
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)  # Bugfix

    def build_config(self, config) -> None:
        Config.setdefaults(
            "postproc",
            {
                "double_tap_time": 250,
                "double_tap_distance": 20,
                "triple_tap_time": 250,
                "triple_tap_distance": 20,
            },
        )

    def config_loggers(self):
        import logging

        for name, _logger in logging.root.manager.loggerDict.items():
            logger.debug(f"{name}: {_logger}")

        urllib_loggers = (
            logging.getLogger("urllib3.connectionpool"),
            logging.getLogger("urllib3.connection"),
            logging.getLogger("urllib3.response"),
        )

        for _logger in urllib_loggers:
            _logger.setLevel(logging.INFO if self.debug_mode else logging.WARNING)

    def _register_error_handlers(self) -> None:
        for handler in self.get_exception_handlers():
            ExceptionManager.add_handler(handler)

    def _configure_window_behavior(self) -> None:
        if self.model.input_mode == "touch":
            Window.softinput_mode = (
                "pan"  # Moves Window content up when keyboard is called
            )

    @staticmethod
    def _configure_clock_behavior() -> None:
        Clock.max_iteration = 30

    def dispatch_to_all_controllers(self, event_type: str):
        for c in self.get_controllers():
            c.dispatch(event_type)

    def create_and_open_dialog(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_dialog(*args, **kwargs)

    def create_and_open_notification(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_notification(*args, **kwargs)

    def switch_screen(self):
        pass

    def on_start(self):
        self.config_loggers()
        self.dispatch_to_all_controllers("on_app_start")

    def on_stop(self):
        self.dispatch_to_all_controllers("on_app_exit")

    @property
    def appname(self):
        """Return the name of the application class."""
        return self.__class__.__name__

    def _check_idle(self, *args):
        if not hasattr(self, "idle_timer"):
            return
        if self.idle_timer is None:
            return
        if monotonic() - self.idle_timer > self.idle_timeout:
            self.idle_timer = None
            self.dispatch("on_idle")

    def install_idle(self, timeout=60):
        """
        Install the idle detector. Default timeout is 60s.
        Once installed, it will check every second if the idle timer
        expired. The timer can be rearmed using :func:`rearm_idle`.
        """

        if monotonic is None:
            logger.exception(
                "{}: Cannot use idle detector, monotonic is missing".format(
                    self.appname
                )
            )
        self.idle_timer = None
        self.idle_timeout = timeout
        logger.info(
            "{}: Install idle detector, {} seconds".format(self.appname, timeout)
        )
        Clock.schedule_interval(self._check_idle, 1)
        self.root.bind(on_touch_down=self.rearm_idle, on_touch_up=self.rearm_idle)

    def rearm_idle(self, *args):
        """Rearm the idle timer."""

        if not hasattr(self, "idle_timer"):
            return
        if self.idle_timer is None:
            self.dispatch("on_wakeup")
        self.idle_timer = monotonic()

    def on_idle(self, *args):
        """Event fired when the application enter the idle mode."""

    def on_wakeup(self, *args):
        """Event fired when the application leaves idle mode."""

    def build(self):
        if not self.debug_mode:
            self.create_initial_screens()

        if self.idle_detection:
            self.install_idle(timeout=self.idle_timeout)

        return super().build()

    async def async_run(self, async_lib="trio"):
        async with trio.open_nursery() as nursery:
            logger.info("%s: Starting Async Kivy app", self.appname)
            self.nursery = nursery
            self._run_prepare()
            await async_runTouchApp(async_lib=async_lib)
            self._stop()
            nursery.cancel_scope.cancel()


class MVCDebugApp(MVCApp):
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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

        self.root = self.get_root()
        self.rebuild(first=True)
        self.screen: BaseAppScreen = self._registrator.get_app_screen()

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

        filename = realpath(filename)
        # Check if it's our own application file.
        try:
            mod = sys.modules[self.__class__.__module__]
            mod_filename = realpath(mod.__file__)
        except Exception:
            mod = None
            mod_filename = None

        # Detect if it's the application class // main.
        if mod_filename == filename:
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
                os._exit(0)

    def _filename_to_module(self, filename: str):
        orig_filename = filename
        rootpath = self.get_root_path()
        if filename.startswith(rootpath):
            filename = filename[len(rootpath) :]
        if filename.startswith("/"):
            filename = filename[1:]
        module = filename[:-3].replace("/", ".")
        logger.debug(
            "{}: Translated {} to {}".format(self.appname, orig_filename, module)
        )
        return module

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
            self.root.clear_widgets()
        for widget in self.fill_root(first=first):
            self.root.add_widget(widget)

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

    def fill_root(self, first: bool) -> Iterable[Widget]:
        if first:
            for spec in self.hotreload_config.screens:
                self.create_screen(
                    spec["name"], create_children=spec["recreate_children"]
                )
                yield self._registrator.get_screen(spec["name"])
        else:
            for spec in self.hotreload_config.screens:
                self.recreate_screen(
                    spec["name"], recreate_children=spec["recreate_children"]
                )
                yield self._registrator.get_screen(spec["name"])
