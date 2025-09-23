from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Literal

import trio
from kivy._event import EventDispatcher
from kivy.app import App
from kivy.base import ExceptionManager, ExceptionHandler, async_runTouchApp
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    ObjectProperty,
    StringProperty,
    BooleanProperty,
    NumericProperty,
    OptionProperty,
)
from kivy.utils import platform as _platform
from kivymd.theming import ThemeManager
from trio import Nursery

from mvckivy.app import ScreenRegistrator
from mvckivy.project_management import PathItem
from mvckivy.project_management.path_manager import MVCPathManager
from mvckivy.utils.builder import MVCBuilder
from mvckivy.utils.constants import (
    Scheme,
    Palette,
    INPUT_MODES,
    DEVICE_TYPES,
    DEVICE_ORIENTATIONS,
    AVAILABLE_PLATFORMS,
    DESKTOP_PLATFORMS,
)
from mvckivy.utils.error_handlers import ClockHandler

try:
    from monotonic import monotonic
except ImportError:
    monotonic = None


if TYPE_CHECKING:
    from mvckivy.base_mvc.base_app_controller import BaseAppController
    from mvckivy.base_mvc.base_app_model import BaseAppModel
    from mvckivy.base_mvc.base_app_screen import BaseAppScreen


original_argv = sys.argv
logger = logging.getLogger("mvckivy")


class PathManagerBehavior:
    def get_root_path(self) -> PathItem:
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
        return PathItem(proj_root)

    def create_path_manager(self) -> MVCPathManager:
        return MVCPathManager(self.get_root_path())


class ScreenRegistrationBehavior:
    _registrator: ObjectProperty[ScreenRegistrator] = ObjectProperty(rebind=False)

    def create_screen_registrator(self) -> ScreenRegistrator:
        raise NotImplementedError()

    def log_screen_register_progress(self, load_info) -> None:
        try:
            name = getattr(load_info, "name")
        except Exception:
            name = None
        if not name and isinstance(load_info, dict):
            name = load_info.get("name", "unknown")
        name = name or "unknown"
        logger.debug(
            "mvckivy: Screen '%s' registered. Progress: %.2f%%",
            name,
            self._calc_screen_loading_progress(load_info, percent=True),
        )

    @staticmethod
    def _calc_screen_loading_progress(load_info, percent=False) -> float:
        try:
            current = getattr(load_info, "current")
            total = getattr(load_info, "total")
        except Exception:
            current = (
                load_info.get("current", 1.0) if isinstance(load_info, dict) else 1.0
            )
            total = load_info.get("total", 1.0) if isinstance(load_info, dict) else 1.0
        total = total or 1.0
        res = round(float(current) / float(total), 1)
        return res * 100.0 if percent else res

    def _consume_and_log(self, generator: Iterable) -> None:
        for report in generator:
            self.log_screen_register_progress(report)

    # Adapters to ScreenRegistrator
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

    # Accessors
    def get_model(self, name: str):
        return self._registrator.get_model(name)

    def get_controller(self, name: str):
        return self._registrator.get_controller(name)

    def get_screen(self, name: str):
        return self._registrator.get_screen(name)

    def get_models(self) -> Iterable:
        return self._registrator.get_models()

    def get_controllers(self) -> Iterable:
        return self._registrator.get_controllers()

    def get_screens(self) -> Iterable:
        return self._registrator.get_screens()

    def load_all_screens_kv_files(self) -> None:
        for p in self._registrator.get_kv_paths().values():
            MVCBuilder.load_all_kv_files(p, directory_filters=["children"])


class ThemeBehavior:
    theme_cls: ObjectProperty[ThemeManager] = ObjectProperty()

    def _bind_and_init_theme_settings(self) -> None:
        self.theme_cls.dynamic_color = True
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.3
        if getattr(self, "model", None) is not None:
            self.model.bind(theme_style=self.switch_theme)
            self.model.bind(primary_palette=self.switch_palette)
            self.model.bind(scheme_name=self.switch_scheme)
            self.switch_theme(None, self.model.theme_style)
            self.switch_palette(None, self.model.primary_palette)
            self.switch_scheme(None, self.model.scheme_name)

    def switch_theme(self, _, theme_style: Literal["Dark", "Light"]):
        self.theme_cls.theme_style = theme_style
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)

    def switch_palette(self, _, primary_palette: Palette):
        self.theme_cls.primary_palette = primary_palette
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)

    def switch_scheme(self, _, scheme_name: Scheme):
        self.theme_cls.dynamic_scheme_name = scheme_name
        self.theme_cls._set_application_scheme(self.theme_cls.primary_palette)


class IdleBehavior:
    __events__ = ["on_idle", "on_wakeup"]

    idle_detection = BooleanProperty(False)
    idle_timeout = NumericProperty(60)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idle_timer: monotonic = None

    def _check_idle(self, *args):
        if not hasattr(self, "idle_timer"):
            return
        if self.idle_timer is None:
            return
        if monotonic() and monotonic() - self.idle_timer > self.idle_timeout:
            self.idle_timer = None
            self.dispatch("on_idle")

    def install_idle(self, timeout=60):
        if monotonic is None:
            logger.exception(
                f"{self.appname}: Cannot use idle detector, monotonic is missing"
            )
        self.idle_timer = None
        self.idle_timeout = timeout
        logger.info(f"{self.appname}: Install idle detector, {timeout} seconds")
        Clock.schedule_interval(self._check_idle, 1)
        self.root.bind(on_touch_down=self.rearm_idle, on_touch_up=self.rearm_idle)

    def rearm_idle(self, *args):
        if not hasattr(self, "idle_timer"):
            return
        if self.idle_timer is None:
            self.dispatch("on_wakeup")
        if monotonic:
            self.idle_timer = monotonic()

    def on_idle(self, *args):
        pass

    def on_wakeup(self, *args):
        pass


class GlobalModalCreationBehavior:
    def create_and_open_dialog(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_dialog(*args, **kwargs)

    def create_and_open_notification(self, *args, **kwargs) -> None:
        return self.screen.create_and_open_notification(*args, **kwargs)


class AppInfoBehavior(EventDispatcher):
    __events__ = ("on_device_profile_changed",)

    platform = OptionProperty(_platform, options=[*AVAILABLE_PLATFORMS, "unknown"])
    device_orientation = OptionProperty("none", options=[*DEVICE_ORIENTATIONS, "none"])
    device_type = OptionProperty("none", options=[*DEVICE_TYPES, "none"])
    input_mode = OptionProperty(
        "mouse" if _platform in DESKTOP_PLATFORMS else "touch",
        options=[*INPUT_MODES, "none"],
    )
    window_size: ObjectProperty[tuple[float, float]] = ObjectProperty(Window.size)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Window.bind(size=self.setter("window_size"))
        self._recalc_trigger = Clock.create_trigger(self._recalc, 0)
        self._emit_trigger = Clock.create_trigger(self._emit, 0)
        self._recalc_trigger()

    def on_device_profile_changed(self, orientation: str, device_type: str) -> None:
        pass

    def on_window_size(self, window: Window, size: tuple[float, float]) -> None:
        self._recalc_trigger()

    def _recalc(self, *_):
        w, h = self.window_size
        self.device_orientation = "landscape" if w > h else "portrait"

        primary, secondary = (w, h) if self.device_orientation == "portrait" else (h, w)
        if primary <= dp(400) and secondary <= dp(800):
            self.device_type = "mobile"
        elif primary <= dp(700) and secondary <= dp(1200):
            self.device_type = "tablet"
        else:
            self.device_type = "desktop"

    def on_device_orientation(self, *_):
        self._emit_trigger()

    def on_device_type(self, *_):
        self._emit_trigger()

    def _emit(self, *_):
        self.dispatch(
            "on_device_profile_changed",
            self.device_orientation,
            self.device_type,
        )


class MKVApp(AppInfoBehavior, IdleBehavior, ThemeBehavior, App):
    debug_mode: BooleanProperty = BooleanProperty(False)
    icon: StringProperty = StringProperty("kivymd/images/logo/kivymd-icon-512.png")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.nursery: Nursery | None = None

        self.theme_cls: ThemeManager = ThemeManager()
        self.theme_cls.bind(
            theme_style=self.theme_cls.update_theme_colors,
            primary_palette=self.theme_cls.set_colors,
        )
        self.theme_cls.set_colors()

        if not self.config:
            self.load_config()  # AppModel contains ConfigParserProperties so utils must be loaded first

        self._configure_window_behavior()
        self._configure_clock_behavior()
        self._register_error_handlers()

        self._bind_and_init_theme_settings()

    @property
    def appname(self):
        """Return the name of the application class."""
        return self.__class__.__name__

    def config_loggers(self):
        import logging as _logging

        for name, _logger in _logging.root.manager.loggerDict.items():
            logger.debug(f"{name}: {_logger}")
        urllib_loggers = (
            _logging.getLogger("urllib3.connectionpool"),
            _logging.getLogger("urllib3.connection"),
            _logging.getLogger("urllib3.response"),
        )
        for _logger in urllib_loggers:
            _logger.setLevel(_logging.INFO if self.debug_mode else _logging.WARNING)

    def _configure_clock_behavior(self) -> None:
        Clock.max_iteration = 30

    def _configure_window_behavior(self) -> None:
        if self.input_mode == "touch":
            Window.softinput_mode = "below_target"

    @classmethod
    def get_exception_handlers(cls) -> list[ExceptionHandler]:
        return [
            ClockHandler(),
        ]

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

    def _register_error_handlers(self) -> None:
        for handler in self.get_exception_handlers():
            ExceptionManager.add_handler(handler)

    def build(self):
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

    def on_start(self):
        self.config_loggers()
        return super().on_start()


class MVCApp(
    PathManagerBehavior,
    ScreenRegistrationBehavior,
    GlobalModalCreationBehavior,
    MKVApp,
):
    model: ObjectProperty[BaseAppModel] = ObjectProperty()
    controller: ObjectProperty[BaseAppController] = ObjectProperty()
    screen: ObjectProperty[BaseAppScreen] = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.path_manager = self.create_path_manager()
        self._registrator: ScreenRegistrator = self.create_screen_registrator()

        MVCBuilder.load_libs_kv_files()
        self.load_all_screens_kv_files()

        self._registrator.create_models_and_controllers()
        self.model: BaseAppModel = self._registrator.get_app_model()
        self.controller: BaseAppController = self._registrator.get_app_controller()
        self.create_app_screen()
        self.screen: BaseAppScreen = self._registrator.get_app_screen()
        self.root = self.get_root()

    def dispatch_to_all_controllers(self, event_type: str):
        for c in self.get_controllers():
            c.dispatch(event_type)

    def switch_screen(self):
        pass

    def on_start(self):
        super().on_start()
        self.dispatch_to_all_controllers("on_app_start")

    def on_stop(self):
        self.dispatch_to_all_controllers("on_app_exit")

    def build(self):
        if not self.debug_mode:
            self.create_initial_screens()

        return super().build()

    def get_root(self):
        return self.screen
