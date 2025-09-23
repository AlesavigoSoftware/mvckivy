from mvckivy.app import AppSchema, ScreenRegistrator
from mvckivy.base_mvc import BaseModel, BaseController
from mvckivy.base_mvc.base_app_controller import BaseAppController
from mvckivy.base_mvc.base_app_model import BaseAppModel
from mvckivy.hotreload_app import MVCDebugApp
from mvckivy.utils.hot_reload_utils import HotReloadConfig
from swap_card_test.menu import AppScreen, InitialScreen


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
                "kv_path": r"C:\Users\alesa\Documents\AlesavigoSoftware\mvckivy\test\swap_card_test\menu.kv",
            },
            {
                "name": "initial_screen",
                "model_cls": BaseModel,
                "controller_cls": BaseController,
                "screen_cls": InitialScreen,
                "children": [],
                "kv_path": None,
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
    DemoApp().run()
