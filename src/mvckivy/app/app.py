from __future__ import annotations

import logging
import sys
import os
from fnmatch import fnmatch
from importlib import reload
from os.path import realpath
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Literal

import trio
from kivy.app import App
from kivy.base import ExceptionManager
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
    DictProperty,
    ListProperty,
)
from kivy.uix.popup import Popup
from kivymd.app import FpsMonitoring
from kivymd.theming import ThemeManager
from kivymd.tools.hotreload.app import original_argv, monotonic
from trio import Nursery

from mvckivy.app import ScreenRegistrator
from mvckivy.utils.clock_handler import ClockHandler
from mvckivy.utils.builder import MVCBuilder

from utility.constants import Scheme, Palette


if TYPE_CHECKING:
    from mvckivy.project_management import PathItem
    from mvckivy.base_mvc import BaseModel, BaseController, BaseScreen
    from mvckivy.base_mvc.base_app_controller import BaseAppController
    from mvckivy.base_mvc.base_app_model import BaseAppModel
    from mvckivy.base_mvc.base_app_screen import BaseAppScreen


logger = logging.getLogger("mvckivy")


class UnsupportedSettingsImplementationException(Exception):
    pass


class MVCApp(App):
    """
    Application class, see :class:`~kivy.app.App` class documentation for more
    information.
    """

    icon: StringProperty = StringProperty("kivymd/images/logo/kivymd-icon-512.png")
    theme_cls: ObjectProperty[ThemeManager] = ObjectProperty()
    debug_mode: BooleanProperty = BooleanProperty(False)

    model: ObjectProperty[BaseAppModel] = ObjectProperty()
    controller: ObjectProperty[BaseAppController] = ObjectProperty()
    screen: ObjectProperty[BaseAppScreen] = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nursery: Nursery | None = None
        self.theme_cls: ThemeManager = ThemeManager()
        self.theme_cls.bind(
            theme_style=self.theme_cls.update_theme_colors,
            primary_palette=self.theme_cls.set_colors,
        )
        self.theme_cls.set_colors()

        if not self.config:
            self.load_config()  # AppModel contains ConfigParserProperties so utils must be loaded first

        MVCBuilder.load_libs_kv_files()
        self._screen_dirs = self.register_screen_dirs()
        self.load_all_screens_kv_files(self._screen_dirs.values())

        self._registrator: ScreenRegistrator = self.create_screen_registrator()
        self._registrator.create_models_and_controllers()
        self.model: BaseAppModel = self._registrator.get_app_model()
        self.controller: BaseAppController = self._registrator.get_app_controller()
        for _registration_report in self._registrator.create_initial_screens():
            logger.debug(
                "mvckivy: Initial screens registration succeeded: %s. Progress: %d%%",
                _registration_report["name"],
                int(
                    _registration_report["current"]
                    / _registration_report["total"]
                    * 100
                ),
            )
        self.screen: BaseAppScreen = self._registrator.get_app_screen()

        self._configure_window_behavior()
        self._configure_clock_behavior()
        self._register_error_handlers()

        self._bind_and_init_theme_settings()

    def build(self):
        self.root = self.get_root()
        return super().build()

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

    def register_screen_dirs(self) -> dict[str, PathItem]:
        raise NotImplementedError()

    def create_screen_registrator(self) -> ScreenRegistrator:
        raise NotImplementedError()

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

    @staticmethod
    def load_all_screens_kv_files(dirs: Iterable[str | Path | PathItem]) -> None:
        """
        Load all KV files from the screen directories.
        This method is called in the constructor of the application class.
        Children excluded from loading, as they are not part of the parent screen and load on them own separately.
        """
        for screen_dir in dirs:
            MVCBuilder.load_all_kv_files(screen_dir, directory_filters=["children"])

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

    @staticmethod
    def _register_error_handlers() -> None:
        handlers = [
            ClockHandler(),
        ]
        for handler in handlers:
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
        self.controller.dispatch(event_type)
        for c in self.controllers.values():
            c.dispatch(event_type)

    def create_and_open_dialog(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_dialog(*args, **kwargs)

    def create_and_open_notification(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_notification(*args, **kwargs)

    def switch_screen(self):
        pass


class MVCDebugApp(MVCApp, FpsMonitoring):
    """HotReload Application class."""

    debug_mode = BooleanProperty(True)
    """
    Control either we activate debugging in the app or not.
    Defaults depend if 'DEBUG' exists in os.environ.

    :attr:`DEBUG` is a :class:`~kivy.properties.BooleanProperty`.
    """

    FOREGROUND_LOCK = BooleanProperty(False)
    """
    If `True` it will require the foreground lock on windows.

    :attr:`FOREGROUND_LOCK` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    KV_FILES = ListProperty()
    """
    List of KV files under management for auto reloader.

    :attr:`KV_FILES` is a :class:`~kivy.properties.ListProperty`
    and defaults to `[]`.
    """

    KV_DIRS = ListProperty()
    """
    List of managed KV directories for autoloader.

    :attr:`KV_DIRS` is a :class:`~kivy.properties.ListProperty`
    and defaults to `[]`.
    """

    AUTORELOADER_PATHS = ListProperty([(".", {"recursive": True})])
    """
    List of path to watch for auto reloading.

    :attr:`AUTORELOADER_PATHS` is a :class:`~kivy.properties.ListProperty`
    and defaults to `([(".", {"recursive": True})]`.
    """

    AUTORELOADER_IGNORE_PATTERNS = ListProperty(["*.pyc", "*__pycache__*"])
    """
    List of extensions to ignore.

    :attr:`AUTORELOADER_IGNORE_PATTERNS` is a :class:`~kivy.properties.ListProperty`
    and defaults to `['*.pyc', '*__pycache__*']`.
    """

    CLASSES = DictProperty()
    """
    Factory classes managed by hotreload.

    :attr:`CLASSES` is a :class:`~kivy.properties.DictProperty`
    and defaults to `{}`.
    """

    IDLE_DETECTION = BooleanProperty(False)
    """
    Idle detection (if True, event on_idle/on_wakeup will be fired).
    Rearming idle can also be done with `rearm_idle()`.

    :attr:`IDLE_DETECTION` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    IDLE_TIMEOUT = NumericProperty(60)
    """
    Default idle timeout.

    :attr:`IDLE_TIMEOUT` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `60`.
    """

    RAISE_ERROR = BooleanProperty(True)
    """
    Raise error.
    When the `DEBUG` is activated, it will raise any error instead
    of showing it on the screen. If you still want to show the error
    when not in `DEBUG`, put this to `False`.

    :attr:`RAISE_ERROR` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `True`.
    """

    __events__ = ["on_idle", "on_wakeup"]

    def build(self):
        if self.DEBUG:
            logger.info("{}: Debug mode activated".format(self.appname))
            self.enable_autoreload()
            self.patch_builder()
            self.bind_key(32, self.rebuild)
        if self.FOREGROUND_LOCK:
            self.prepare_foreground_lock()

        self.state = None
        self.approot = None
        self.root = self.get_root()
        self.rebuild(first=True)

        if self.IDLE_DETECTION:
            self.install_idle(timeout=self.IDLE_TIMEOUT)

        return super().build()

    def unload_app_dependencies(self):
        """
        Called when all the application dependencies must be unloaded.
        Usually happen before a reload
        """

        for path_to_kv_file in self.KV_FILES:
            path_to_kv_file = realpath(path_to_kv_file)
            Builder.unload_file(path_to_kv_file)

        for name, module in self.CLASSES.items():
            Factory.unregister(name)

        for path in self.KV_DIRS:
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

        for path_to_kv_file in self.KV_FILES:
            path_to_kv_file = realpath(path_to_kv_file)
            Builder.load_file(path_to_kv_file)

        for name, module in self.CLASSES.items():
            Factory.register(name, module=module)

        for path in self.KV_DIRS:
            for path_to_dir, dirs, files in os.walk(path):
                for name_file in files:
                    if os.path.splitext(name_file)[1] == ".kv":
                        path_to_kv_file = os.path.join(path_to_dir, name_file)
                        Builder.load_file(path_to_kv_file)

    @mainthread
    def set_error(self, exc, tb=None):
        print(tb)
        from kivy.core.window import Window
        from kivy.utils import get_color_from_hex

        scroll = Factory.MDScrollView(
            scroll_y=0, md_bg_color=get_color_from_hex("#e50000")
        )
        lbl = Factory.Label(
            text_size=(Window.width - 100, None),
            size_hint_y=None,
            text="{}\n\n{}".format(exc, tb or ""),
        )
        lbl.bind(texture_size=lbl.setter("size"))
        scroll.add_widget(lbl)
        self.set_widget(scroll)

    def bind_key(self, key, callback):
        """Bind a key (keycode) to a callback (cannot be unbind)."""

        from kivy.core.window import Window

        def _on_keyboard(window, keycode, *args):
            if key == keycode:
                return callback()

        Window.bind(on_keyboard=_on_keyboard)

    @property
    def appname(self):
        """Return the name of the application class."""

        return self.__class__.__name__

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
            logger.info("App: Foreground lock activated")
        except Exception:
            logger.warning("App: No foreground lock available")

    def set_widget(self, wid):
        """
        Clear the root container, and set the new approot widget to `wid`.
        """

        self.root.clear_widgets()
        self.approot = wid
        if wid is None:
            return
        self.root.add_widget(self.approot)
        try:
            wid.do_layout()
        except Exception:
            pass

    # State management.
    def apply_state(self, state):
        """Whatever the current state is, reapply the current state."""

    # Idle management leave.
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

    # Internals.
    def patch_builder(self):
        Builder.orig_load_string = Builder.load_string
        Builder.load_string = self._builder_load_string

    def on_idle(self, *args):
        """Event fired when the application enter the idle mode."""

    def on_wakeup(self, *args):
        """Event fired when the application leaves idle mode."""

    @mainthread
    def _reload_from_watchdog(self, event):
        from watchdog.events import FileModifiedEvent

        if not isinstance(event, FileModifiedEvent):
            return

        for pat in self.AUTORELOADER_IGNORE_PATTERNS:
            if fnmatch(event.src_path, pat):
                return

        if event.src_path.endswith(".py"):
            # source changed, reload it
            try:
                Builder.unload_file(event.src_path)
                self._reload_py(event.src_path)
            except Exception as e:
                import traceback

                self.set_error(repr(e), traceback.format_exc())
                return

        Clock.unschedule(self.rebuild)
        Clock.schedule_once(self.rebuild, 0.1)

    def _builder_load_string(self, string, **kwargs):
        if "filename" not in kwargs:
            from inspect import getframeinfo, stack

            caller = getframeinfo(stack()[1][0])
            kwargs["filename"] = caller.filename
        return Builder.orig_load_string(string, **kwargs)

    def _check_idle(self, *args):
        if not hasattr(self, "idle_timer"):
            return
        if self.idle_timer is None:
            return
        if monotonic() - self.idle_timer > self.idle_timeout:
            self.idle_timer = None
            self.dispatch("on_idle")

    def _reload_py(self, filename):
        # We don't have dependency graph yet, so if the module actually exists
        # reload it.

        filename = realpath(filename)
        # Check if it's our own application file.
        try:
            mod = sys.modules[self.__class__.__module__]
            mod_filename = realpath(mod.__file__)
        except Exception:
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

    def _filename_to_module(self, filename):
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

    @mainthread
    def set_error(self, exc, tb=None):
        logger.warning(tb)
        if self.debug_mode:
            from kivy.core.window import Window
            from kivy.utils import get_color_from_hex

            p = Factory.Popup(title="Exception caught!", size_hint=(0.9, 0.9))
            scroll = Factory.MDScrollView(
                scroll_y=0, md_bg_color=get_color_from_hex("#e50000")
            )
            box = Factory.MDBoxLayout(orientation="vertical")
            lbl = Factory.Label(
                text_size=(Window.width - 100, None),
                size_hint_y=None,
                text="{}\n\n{}".format(exc, tb or ""),
            )
            cls_btn = Factory.MDButton(
                Factory.MDButtonText(text="Закрыть"),
                style="elevated",
                on_release=lambda *_: p.dismiss(),
            )

            lbl.bind(texture_size=lbl.setter("size"))

            box.add_widget(lbl)
            box.add_widget(cls_btn)
            scroll.add_widget(box)
            p.content = scroll
            p._open()

    def enable_autoreload(self):
        """
        Enable autoreload manually. It is activated automatically
        if "DEBUG" exists in environ. It requires the `watchdog` module.
        """

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.warning("{}: Auto reloader is missing watchdog".format(self.appname))
            return
        logger.info("{}: Auto reloader activated".format(self.appname))
        self.w_handler = handler = FileSystemEventHandler()
        handler.dispatch = self._reload_from_watchdog
        self._observer = observer = Observer()
        for path in self.AUTORELOADER_PATHS:
            options = {"recursive": True}
            if isinstance(path, (tuple, list)):
                path, options = path
            observer.schedule(handler, path, **options)
        observer.start()

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

    def on_start(self):
        self.config_loggers()

    def on_stop(self) -> None:
        self.dispatch_to_all_controllers("on_app_exit")

    # End utility block

    # Begin build block

    def rebuild(self, *args, first: bool = False, **kwargs):
        logger.info(f"{self.appname}: Rebuilding the application")
        try:
            self.unload_app_dependencies()

            Builder.rulectx = {}

            self.load_app_dependencies()
            self.set_widget(None)
            self.approot = self.build_app(first=first)
            self.set_widget(self.approot)
            self.apply_state(self.state)
        except Exception as exc:
            import traceback

            logger.exception("{}: Error when building app".format(self.appname))
            self.set_error(repr(exc), traceback.format_exc())
            if not self.DEBUG and self.RAISE_ERROR:
                raise

    def build_app(self, first=False) -> BaseScreen:
        if not first:
            self.app_screen.external_screen_manager.clear_widgets()

        self._fill_external_screen_manager()

        if not first:
            self.on_start()

        return self.app_screen

    def build(self):
        if not self.debug_mode:
            return self.build_app(first=True)

        self._set_reload_params()
        self.DEBUG = True
        self.fps_monitor_start()
        super().build()  # hotreload.MDApp calls build_app

    async def async_run(self, async_lib="trio"):
        async with trio.open_nursery() as nursery:
            logger.info("Reloader: Starting Async Kivy app")
            self.nursery = nursery
            self._run_prepare()
            await async_runTouchApp(async_lib=async_lib)
            self._stop()
            nursery.cancel_scope.cancel()

    # End build block


if __name__ == "__main__":
    from kivy.app import async_runTouchApp

    async_runTouchApp(MVCApp().run(), async_lib="trio")
