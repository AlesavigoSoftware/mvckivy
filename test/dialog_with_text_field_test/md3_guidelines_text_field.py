from __future__ import annotations
from dataclasses import dataclass

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    NumericProperty,
    DictProperty,
    BooleanProperty,
    StringProperty,
)
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivy.animation import Animation


# брейкпоинты (адаптация раскладки, не шрифтов)
COMPACT_MAX = 600
MEDIUM_MAX = 840


@dataclass
class FormDensity:
    vgap: float
    hgap: float
    padding_h: float
    padding_v: float


DENSITY_DEFAULT = FormDensity(
    vgap=dp(16), hgap=dp(16), padding_h=dp(20), padding_v=dp(18)
)
DENSITY_COMPACT = FormDensity(
    vgap=dp(10), hgap=dp(12), padding_h=dp(18), padding_v=dp(14)
)


class ConnectCard(MDCard):
    cols = NumericProperty(1)
    density: DictProperty = DictProperty({})
    compact_helpers = BooleanProperty(True)
    title = StringProperty("Подключение к наземной станции")
    icon_name = StringProperty("access-point-network")
    max_width = NumericProperty(dp(560))
    use_compact_title = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._apply(Window.size)
        Window.bind(size=lambda *_: self._apply(Window.size))

    def _apply(self, size):
        w, _ = size
        if w < COMPACT_MAX:
            self.cols = 1
            d = DENSITY_DEFAULT
            self.compact_helpers = True
        elif w < MEDIUM_MAX:
            self.cols = 2
            d = DENSITY_COMPACT
            self.compact_helpers = True
        else:
            self.cols = 2
            d = DENSITY_DEFAULT
            self.compact_helpers = False

        self.use_compact_title = w < 420
        self.density = {
            "vgap": d.vgap,
            "hgap": d.hgap,
            "padding_h": d.padding_h,
            "padding_v": d.padding_v,
        }


KV = r"""
#:import dp kivy.metrics.dp
#:import Window kivy.core.window.Window

<ConnectCard>:
    size_hint: None, None
    width: min(root.max_width, Window.width * 0.94)
    adaptive_height: True
    radius: [dp(22)]
    elevation: 3
    md_bg_color: app.theme_cls.surfaceContainerLowestColor
    padding: root.density["padding_h"], root.density["padding_v"]
    orientation: "vertical"

    # Шапка
    MDBoxLayout:
        spacing: dp(12)
        size_hint_y: None
        adaptive_height: True
        padding: 0, dp(2)

        MDBoxLayout:
            size_hint: None, None
            width: dp(36)
            height: dp(36)
            pos_hint: {"center_y": .5}
            radius: [dp(18)]
            md_bg_color: app.theme_cls.surfaceContainerHighColor
            MDIcon:
                icon: root.icon_name
                pos_hint: {"center_x": .5, "center_y": .5}
                theme_text_color: "Custom"
                text_color: app.theme_cls.onSurfaceVariantColor

        MDLabel:
            text: root.title
            font_style: "Title"
            role: "medium" if root.use_compact_title else "large"
            max_lines: 2
            adaptive_height: True
            text_size: self.width, None
            valign: "center"
            halign: "left"
            pos_hint: {"center_y": .5}

    # Поля
    MDGridLayout:
        cols: root.cols
        spacing: root.density["hgap"], root.density["vgap"]
        size_hint_y: None
        height: self.minimum_height
        adaptive_height: True

        MDTextField:
            mode: "filled"
            text: "127.0.0.1"
            MDTextFieldHintText:
                text: "IP (по умолчанию 127.0.0.1)" if root.compact_helpers else "IP наземной станции"
            MDTextFieldHelperText:
                text: "По умолчанию: 127.0.0.1"
                mode: "on_error"

        MDTextField:
            mode: "filled"
            text: "8000"
            input_filter: "int"
            MDTextFieldHintText:
                text: "Порт (по умолчанию 80)" if root.compact_helpers else "Номер порта"
            MDTextFieldHelperText:
                text: "По умолчанию: 80"
                mode: "on_error"

    # Действия
    MDBoxLayout:
        size_hint_y: None
        height: dp(52)
        spacing: dp(8)
        MDWidget:
        MDButton:
            style: "text"
            on_release: app.on_register()
            MDButtonText:
                text: "Регистрация"
        MDButton:
            style: "outlined"
            on_release: app.on_connect()
            MDButtonText:
                text: "Подключиться"

# Экран: «стек» карточки и прогресса, центрируем весь блок
MDScreen:
    md_bg_color: app.theme_cls.backgroundColor

    AnchorLayout:
        anchor_x: "center"
        anchor_y: "center"

        MDBoxLayout:
            id: stack
            orientation: "vertical"
            size_hint: None, None
            width: min(dp(560), Window.width * 0.94)
            adaptive_height: True
            spacing: dp(12)

            ConnectCard:
                id: connect_card

            # НОВЫЙ API: MDLinearProgressIndicator
            MDLinearProgressIndicator:
                id: loader
                type: "determinate"        # режим: детерминированный
                value: 0                   # с 0 до 100
                indicator_color: app.theme_cls.primaryColor
                track_color: app.theme_cls.surfaceVariantColor
                size_hint_x: 1
                size_hint_y: None
                height: 0                  # по умолчанию скрыта
                opacity: 0
"""


class App(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    # --- действия ---
    def on_register(self):
        print("Навигация: регистрация")

    def on_connect(self):
        self.show_loader(duration=1.6)

    # --- прогресс по новому API (KivyMD 2.0) ---
    def show_loader(self, duration: float = 1.6):
        bar = self.root.ids.loader
        # показать и сбросить
        Animation.cancel_all(bar)
        bar.value = 0
        bar.opacity = 1
        bar.height = dp(4)

        # детерминированная анимация до 100, затем скрыть и обнулить
        anim = Animation(value=100, d=duration, t="out_quad")
        anim.bind(on_complete=lambda *_: self._hide_loader())
        anim.start(bar)

    def _hide_loader(self):
        bar = self.root.ids.loader
        fade = Animation(opacity=0, d=0.15)
        fade.bind(on_complete=lambda *_: self._reset_loader())
        fade.start(bar)

    def _reset_loader(self):
        bar = self.root.ids.loader
        bar.height = 0
        bar.value = 0
        # optional: bar.type = None  # если хотите полностью остановить любые внешние start()


if __name__ == "__main__":
    App().run()
