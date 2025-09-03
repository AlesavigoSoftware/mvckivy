from __future__ import annotations

import functools
import logging
import time
from typing import (
    Callable,
    Type,
    Generator,
    Concatenate,
    ParamSpec,
    TypeVar,
    TYPE_CHECKING,
    Iterable,
)
from dataclasses import dataclass

from mvckivy.base_mvc.base_app_controller import BaseAppController
from mvckivy.base_mvc.base_app_model import BaseAppModel
from mvckivy.base_mvc.base_app_screen import BaseAppScreen
from mvckivy.project_management import PathItem

if TYPE_CHECKING:
    from mvckivy.utils.typing import (
        BaseModel,
        BaseController,
        BaseScreen,
        ScreensSchema,
    )


logger = logging.getLogger("mvckivy")


R = TypeVar("R")
P = ParamSpec("P")


def log_registration(
    func: Callable[Concatenate[MVCTrio, P], R],
) -> Callable[Concatenate[MVCTrio, P], R]:
    """
    Decorator that logs the registration of models, controllers, or screens.

    The decorated ``func`` must be a bound method with signature
    ``(self, *args)`` and can return any type ``R``.
    """

    @functools.wraps(func)
    def wrapper(self: MVCTrio, *args: P.args) -> R:
        start = time.perf_counter()
        result = func(self, *args)
        elapsed_ms = (time.perf_counter() - start) * 1_000

        object_type = func.__name__.replace("ensure_", "")
        logger.debug(
            "%s '%s' successfully registered in %.3f ms",
            object_type.capitalize(),
            self.name,
            elapsed_ms,
        )
        return result

    return wrapper


class MVCTrio:
    def __init__(
        self,
        name: str,
        model_cls: Type[BaseModel],
        controller_cls: Type[BaseController],
        screen_cls: Type[BaseScreen],
        children: list[str],
        parent: str | None,
        kv_path: PathItem | None,
    ):
        self.name = name
        self._model_cls = model_cls
        self._controller_cls = controller_cls
        self._screen_cls = screen_cls
        self._kv_path = kv_path

        self._children = children
        self._parent = parent

        self._model: BaseModel | None = None
        self._controller: BaseController | None = None
        self._screen: BaseScreen | None = None

    @log_registration
    def ensure_model(self) -> BaseModel:
        if self._model is None:
            self._model = self._model_cls()
        return self._model

    @log_registration
    def ensure_controller(self) -> BaseController:
        if self._controller is None:
            self._controller = self._controller_cls(model=self.ensure_model())
        return self._controller

    @log_registration
    def ensure_screen(self) -> BaseScreen:
        if self._screen is None:
            self._screen = self._screen_cls(
                model=self.ensure_model(),
                controller=self.ensure_controller(),
                name=self.name,
            )
        return self._screen

    def get_model(self) -> BaseModel | None:
        return self._model

    def get_controller(self) -> BaseController | None:
        return self._controller

    def get_screen(self) -> BaseScreen | None:
        return self._screen

    @property
    def parent(self) -> str | None:
        return self._parent

    @property
    def children(self) -> list[str]:
        return self._children

    @property
    def kv_path(self) -> PathItem | None:
        return self._kv_path

    def clear_screen(self) -> None:
        self._screen = None

    def clear_controller(self) -> None:
        self._controller = None

    def clear_model(self) -> None:
        self._model = None


@dataclass(frozen=True)
class ScreenRegistrationReport:
    """
    Unified payload for reporting screen registration progress.

    Centralizes what we expose to callers, so extending the data later
    requires changing only one factory method instead of all call sites.
    """

    name: str
    current: int
    total: int
    instance: BaseScreen | None


class ScreenRegistrator:
    APP_SCREEN_NAME = "app_screen"

    def __init__(self, schema: list[ScreensSchema]):
        self.trios: dict[str, MVCTrio] = {t["name"]: MVCTrio(**t) for t in schema}

    def _trio(self, name: str) -> MVCTrio | None:
        return self.trios.get(name)

    def get_root(self):
        return self.get_screen(self.APP_SCREEN_NAME)

    def get_app_model(self) -> BaseAppModel | None:
        return self._trio(self.APP_SCREEN_NAME).get_model()

    def get_app_controller(self) -> BaseAppController | None:
        return self._trio(self.APP_SCREEN_NAME).get_controller()

    def get_app_screen(self) -> BaseAppScreen | None:
        return self._trio(self.APP_SCREEN_NAME).get_screen()

    def get_model(self, name: str) -> BaseModel | None:
        return self._trio(name).get_model()

    def get_controller(self, name: str) -> BaseController | None:
        return self._trio(name).get_controller()

    def get_screen(self, name: str) -> BaseScreen | None:
        return self._trio(name).get_screen()

    def get_models(self) -> list[BaseModel]:
        return [t.get_model() for t in self.trios.values() if t.get_model() is not None]

    def get_controllers(self) -> list[BaseController]:
        return [
            t.get_controller()
            for t in self.trios.values()
            if t.get_controller() is not None
        ]

    def get_screens(self) -> list[BaseScreen]:
        return [
            t.get_screen() for t in self.trios.values() if t.get_screen() is not None
        ]

    def get_kv_paths(self) -> dict[str, PathItem]:
        return {
            name: t.kv_path for name, t in self.trios.items() if t.kv_path is not None
        }

    def create_models_and_controllers(self) -> None:
        for t in self.trios.values():
            t.clear_controller()
            t.clear_model()
            t.ensure_model()
            t.ensure_controller()

    def _attach_to_parent(self, name: str, screen: BaseScreen) -> None:
        parent_name = self.trios[name].parent
        if not parent_name:
            return
        parent_trio = self.trios[parent_name]
        parent_screen = parent_trio.get_screen() or parent_trio.ensure_screen()
        parent_screen.add_widget(screen)

    def _create_and_attach(self, name: str) -> BaseScreen:
        trio = self.trios[name]
        screen = trio.get_screen()
        if screen is None:
            screen = trio.ensure_screen()
            self._attach_to_parent(name, screen)
        return screen

    def _report(self, name: str, current: int, total: int) -> ScreenRegistrationReport:
        """
        Single construction point for progress reports.
        """
        return ScreenRegistrationReport(
            name=name,
            current=current,
            total=total,
            instance=self.get_screen(name),
        )

    def create_app_screen(self) -> Generator[ScreenRegistrationReport, None, None]:
        name = self.APP_SCREEN_NAME
        if name not in self.trios:
            raise ValueError("'app_screen' is not registered")
        if self.trios[name].get_screen() is not None:
            raise ValueError("'app_screen' already exists")
        self._create_and_attach(name)
        yield self._report(name, 1, 1)

    def create_initial_screens(self) -> Generator[ScreenRegistrationReport, None, None]:
        init = "initial_screen"
        if init not in self.trios:
            raise ValueError("'initial_screen' is not registered")
        plan = [init] + self.trios[init].children
        total = len(plan)
        for i, name in enumerate(plan, 1):
            if self.trios[name].get_screen() is not None:
                raise ValueError(f"Screen '{name}' already exists")
            self._create_and_attach(name)
            yield self._report(name, i, total)

    def create_all_screens(self) -> Generator[ScreenRegistrationReport, None, None]:
        created = {n for n, t in self.trios.items() if t.get_screen() is not None}
        pending = [n for n in self.trios.keys() if n not in created]
        total = len(pending)
        for i, name in enumerate(pending, 1):
            self._create_and_attach(name)
            yield self._report(name, i, total)

    def create_screen(
        self, name: str, *, create_children=False
    ) -> Generator[ScreenRegistrationReport, None, None]:
        """
        Creates a screen by name, optionally creating its children as well. Uses in HotReload only.
        :param name:
        :param create_children:
        :return:
        """
        if name not in self.trios:
            raise ValueError(f"Screen '{name}' is not registered")
        # Ensure the target screen does not already exist
        if self.trios[name].get_screen() is not None:
            raise ValueError(f"Screen '{name}' already exists")

        self._create_and_attach(name)
        yield self._report(name, 1, 1)
        if create_children:
            children_names = self.trios[name].children
            total = len(children_names)
            for i, child in enumerate(children_names, 1):
                # Ensure each child does not already exist before creation
                if self.trios[child].get_screen() is not None:
                    raise ValueError(f"Child screen '{child}' already exists")
                self._create_and_attach(child)
                yield self._report(child, i, total)

    def recreate_screen(
        self, name: str, *, recreate_children: bool = False
    ) -> Generator[ScreenRegistrationReport, None, None]:
        """
        Recreates a screen by name, optionally recreating its children as well. Uses in HotReload only.
        :param name:
        :param recreate_children:
        :return:
        """
        if name not in self.trios:
            raise ValueError(f"Screen '{name}' is not registered")

        trio = self.trios[name]
        children_names = trio.children

        if recreate_children:
            total = len(children_names) + 1
            step = 0

            # Recreate children first (in-place under current parent)
            for child in children_names:
                for _ in self.recreate_screen(child, recreate_children=True):
                    pass
                step += 1
                yield self._report(child, step, total)

            # Transfer children from old parent to new parent
            old_screen = trio.get_screen()
            old_parent = old_screen.parent if old_screen else None

            # collect current child instances (after their recreation)
            current_children: list[BaseScreen] = []
            if old_screen:
                for child in children_names:
                    cs = self.trios[child].get_screen()
                    if cs and cs in old_screen.children:
                        current_children.append(cs)
                        old_screen.remove_widget(cs)

            # recreate self
            if old_parent and old_screen:
                old_parent.remove_widget(old_screen)
            trio.clear_screen()
            new_screen = trio.ensure_screen()
            if old_parent:
                old_parent.add_widget(new_screen)
            else:
                self._attach_to_parent(name, new_screen)

            # reattach children to the new screen
            for cs in current_children:
                new_screen.add_widget(cs)

            step += 1
            yield self._report(name, step, total)
            return

        # --- preserve children (do not recreate them) ---
        old_screen = trio.get_screen()
        old_parent = old_screen.parent if old_screen else None

        detached: list[BaseScreen] = []
        if old_screen:
            for child_name in children_names:
                child_screen = self.trios[child_name].get_screen()
                if child_screen and child_screen in old_screen.children:
                    old_screen.remove_widget(child_screen)
                    detached.append(child_screen)

        if old_parent and old_screen:
            old_parent.remove_widget(old_screen)

        trio.clear_screen()
        new_screen = trio.ensure_screen()

        if trio.parent:
            if old_parent:
                old_parent.add_widget(new_screen)
            else:
                self._attach_to_parent(name, new_screen)

        # Reattach children back (create missing if needed)
        for child_name in children_names:
            child_trio = self.trios[child_name]
            cs = child_trio.get_screen() or child_trio.ensure_screen()
            new_screen.add_widget(cs)

        yield self._report(name, 1, 1)
