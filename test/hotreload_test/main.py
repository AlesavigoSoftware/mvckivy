from pathlib import Path
import trio

from mvckivy.app import ScreenRegistrator, MVCDebugApp, MVCApp
from mvckivy.project_management.path_manager import MVCPathManager, PathItem
from mvckivy.app.screens_schema import AppSchema
from mvckivy.base_mvc import BaseModel, BaseController, BaseScreen
from mvckivy.base_mvc.base_app_controller import BaseAppController
from mvckivy.base_mvc.base_app_model import BaseAppModel
from mvckivy.base_mvc.base_app_screen import BaseAppScreen
from mvckivy.utils.hot_reload_utils import HotReloadConfig


class AppScreen(BaseAppScreen):
    pass


class InitialScreen(BaseScreen):
    pass


class DemoAppSchema(AppSchema):
    @classmethod
    def create_schema(cls) -> list[dict[str, str | type]]:
        return [
            {
                "name": "app_screen",
                "model_cls": BaseAppModel,
                "controller_cls": BaseAppController,
                "screen_cls": AppScreen,
                "children": ["initial_screen"],
            },
            {
                "name": "initial_screen",
                "model_cls": BaseModel,
                "controller_cls": BaseController,
                "screen_cls": InitialScreen,
                "children": [],
            },
        ]


class DemoApp(MVCDebugApp):
    def create_screen_registrator(self) -> ScreenRegistrator:
        return ScreenRegistrator(DemoAppSchema.get_schema())

    def fill_hotreload_config(
        self, hotreload_config: HotReloadConfig
    ) -> HotReloadConfig:
        return hotreload_config.from_manual(
            autoreloader_paths=[
                (
                    self.path_manager.proj_dir.str(),
                    {"recursive": True},
                ),
            ],
            kv_dirs=[self.path_manager.proj_dir.str()],
            screens=[{"name": "initial_screen", "recreate_children": True}],
        )


if __name__ == "__main__":
    trio.run(DemoApp().async_run, "trio")
