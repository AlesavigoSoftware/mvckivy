from __future__ import annotations

import trio
from kivy.properties import ObjectProperty
from kivy.weakproxy import WeakProxy

from mvckivy.app import MVCApp
from mvckivy.app.screen_registrator import ScreenRegistrator
from mvckivy.app.screens_schema import AppSchema
from mvckivy.base_mvc import BaseScreen
from mvckivy.base_mvc.base_app_screen import BaseAppScreen

from mvckivy.project_management import PathItem
from mvckivy.uix.settings import MDSettings
from utility.path_manager import PathManager


class AppScreen(BaseAppScreen):
    pass


class InitialScreen(BaseScreen):
    settings: ObjectProperty[WeakProxy[MDSettings] | None] = ObjectProperty(
        None, allownone=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Панель настроек приложения
        self.settings.create_and_add_panel_to_interface(
            "Интерфейс",
            data=[
                {"type": "title", "title": "Язык и единицы измерения"},
                {
                    "type": "options",
                    "title": "Выберите язык",
                    "desc": "В бета-версии приложения доступен только русский язык",
                    "key": "app_language",
                    "options": ["Русский", "English"],
                },
                {
                    "type": "options",
                    "title": "Единицы измерения",
                    "desc": "В бета-версии приложения доступны только единицы СИ",
                    "key": "measurements",
                },
                {"type": "title", "title": "Внешний вид"},
                {
                    "type": "bool",
                    "title": "Темная тема",
                    "desc": "Позволяет изменить тему приложения на темную. Все настройки палитр при этом инвертируются.",
                    "key": "theme",
                },
                {
                    "type": "options",
                    "title": "Палитра приложения",
                    "desc": "Позволяет изменить активную палитру приложения.",
                    "key": "primary_palette",
                    "options": [""],
                },
                {
                    "type": "options",
                    "title": "Цветовая схема",
                    "desc": "Позволяет изменить цветовую схему приложения. Например: черно-белая.",
                    "key": "scheme_name",
                    "options": [""],
                },
            ],
        )

        self.settings.create_and_add_panel_to_interface(
            "Отображение карт",
            data=[
                {"type": "title", "title": "Интерфейс"},
                {
                    "type": "bool",
                    "title": "Центрировать карту на БПЛА",
                    "desc": "Автоматическое отслеживание позиции аппарата",
                    "key": "map_centered",
                },
                {
                    "type": "bool",
                    "title": "Оффлайн-карты",
                    "desc": "Использовать локальные карты без интернета",
                    "key": "offline_maps",
                },
            ],
        )

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MDSettings):
            self.settings = WeakProxy(widget)
        super().add_widget(widget, *args, **kwargs)

    def remove_widget(self, widget) -> None:
        if isinstance(widget, MDSettings):
            self.settings = None
        super().remove_widget(widget)


class TestAgroFlowAppSchema(AppSchema):
    @classmethod
    def create_schema(cls) -> list[dict[str, str | type]]:
        from mvckivy.base_mvc.base_app_model import BaseAppModel
        from mvckivy.base_mvc.base_app_controller import BaseAppController
        from mvckivy.base_mvc.base_model import BaseModel
        from mvckivy.base_mvc.base_controller import BaseController

        return [
            {
                "name": "app_screen",
                "model_cls": BaseAppModel,
                "controller_cls": BaseAppController,
                "screen_cls": AppScreen,
                "children": ["initial_screen"],
                "kv_path": r"C:\Users\alesa\Documents\AlesavigoSoftware\agro-flow-app\test\settings_test\app_screen",
            },
            {
                "name": "initial_screen",
                "model_cls": BaseModel,
                "controller_cls": BaseController,
                "screen_cls": InitialScreen,
                "children": [],
                "kv_path": r"C:\Users\alesa\Documents\AlesavigoSoftware\agro-flow-app\test\settings_test\initial_screen",
            },
        ]


class TestAgroFlowApp(MVCApp):
    def create_screen_registrator(self) -> ScreenRegistrator:
        """
        Create a ScreenRegistrator instance with the schema from AgroFlowAppSchema.
        """
        return ScreenRegistrator(TestAgroFlowAppSchema.get_schema())

    def register_screen_dirs(self) -> dict[str, PathItem]:
        """
        Register screen directories based on the schema from AgroFlowAppSchema.
        This method is called during the initialization of the AgroFlowApp.
        """
        return PathManager.register_screen_dirs(TestAgroFlowAppSchema.get_schema())


if __name__ == "__main__":
    trio.run(TestAgroFlowApp().async_run, "trio")
