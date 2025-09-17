from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.core.window import Window
from kivy.properties import ObjectProperty, Clock
from mvckivy.base_mvc import BaseController

if TYPE_CHECKING:
    from mvckivy.base_mvc.base_app_model import BaseAppModel


class BaseAppController(BaseController):
    model: ObjectProperty[BaseAppModel] = ObjectProperty()

    def dispatch_theme_style(
        self, theme_style: str = "Light", toggle=False, force_dispatch=False
    ):
        if toggle:
            self.dispatch_to_model(
                theme_style="Light" if self.model.theme_style == "Dark" else "Dark",
                force_dispatch=force_dispatch,
            )
            return

        self.dispatch_to_model(theme_style=theme_style, force_dispatch=force_dispatch)

    def dispatch_primary_palette(self, primary_palette: str, force_dispatch=False):
        self.dispatch_to_model(
            primary_palette=primary_palette, force_dispatch=force_dispatch
        )

    def dispatch_scheme_name(self, scheme_name: str, force_dispatch=False):
        self.dispatch_to_model(scheme_name=scheme_name, force_dispatch=force_dispatch)
