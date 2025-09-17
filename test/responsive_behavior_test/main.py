from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    NumericProperty,
    StringProperty,
    DictProperty,
    BooleanProperty,
)
from kivy.clock import Clock
from kivy.factory import Factory

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)


# -------------------- Size classes (MD3) --------------------


def px_to_dp(px: float) -> float:
    return px / dp(1)


WidthClass = Literal["compact", "medium", "expanded"]
HeightClass = Literal["compact", "medium", "expanded"]


def classify_width(w_dp: float) -> WidthClass:
    if w_dp < 600:
        return "compact"
    if w_dp < 840:
        return "medium"
    return "expanded"


def classify_height(h_dp: float) -> HeightClass:
    if h_dp < 480:
        return "compact"
    if h_dp < 900:
        return "medium"
    return "expanded"


# -------------------- Density профили --------------------


@dataclass
class Density:
    vgap: float
    hgap: float
    section_gap: float
    list_row_gap: float


DENSITY_DEFAULT = Density(
    vgap=dp(16), hgap=dp(16), section_gap=dp(24), list_row_gap=dp(8)
)
DENSITY_COMPACT = Density(
    vgap=dp(12), hgap=dp(12), section_gap=dp(16), list_row_gap=dp(4)
)  # –1..–2


# -------------------- KV-шаблоны --------------------

KV = r"""
#:import dp kivy.metrics.dp

<SurfaceCard@MDCard>:
    radius: [dp(24)]
    padding: dp(16)
    elevation: 2
    md_bg_color: app.theme_cls.surfaceContainerLowestColor
    adaptive_height: True

<NavigationRail@MDBoxLayout>:
    orientation: "vertical"
    size_hint_x: None
    width: dp(72)
    padding: dp(8)
    spacing: dp(8)
    md_bg_color: app.theme_cls.surfaceContainerColor
    MDButton:
        style: "text"
        MDButtonIcon: 
            icon: "home"
    MDButton:
        style: "text"
        MDButtonIcon: 
            icon: "map"
    MDButton:
        style: "text"
        MDButtonIcon:
            icon: "bell"

<BottomBar@MDBoxLayout>:
    size_hint_y: None
    height: dp(64)
    padding: dp(8)
    spacing: dp(8)
    md_bg_color: app.theme_cls.surfaceContainerColor
    MDButton:
        style: "text"
        MDButtonIcon: 
            icon: "home"
        MDButtonText: 
            text: "Главная"
    MDButton:
        style: "text"
        MDButtonIcon: 
            icon: "map"
        MDButtonText: 
            text: "Карта"
    MDButton:
        style: "text"
        MDButtonIcon: 
            icon: "bell"
        MDButtonText: 
            text: "Оповещения"

<SideSheet@MDCard>:
    radius: [dp(24), 0, 0, dp(24)]
    size_hint_x: None
    width: dp(360)
    md_bg_color: app.theme_cls.surfaceContainerColor
    elevation: 3
    padding: dp(16)

<ResponsiveRoot>:
    orientation: "vertical"
    md_bg_color: app.theme_cls.backgroundColor

    # Header
    MDBoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(12), 0
        md_bg_color: app.theme_cls.surfaceContainerColor
        MDLabel:
            text: "ResponsiveLayout — MD3"
            font_style: "Title"
            role: "large"
        MDBoxLayout:
            size_hint_x: None
            width: dp(200)
            padding: 0, dp(8), 0, 0
            MDButton:
                style: "outlined"
                on_release: root.on_show_notifications()
                MDButtonIcon: 
                    icon: "bell"
                MDButtonText: 
                    text: "Уведомления"

    # Основная область — сюда из Python добавим три слота: слева/центр/справа
    MDBoxLayout:
        id: body
        spacing: dp(16)
        padding: dp(16)
"""


# -------------------- Корневой виджет --------------------


class ResponsiveRoot(MDBoxLayout):
    width_class: StringProperty = StringProperty("compact")
    height_class: StringProperty = StringProperty("medium")
    cols: NumericProperty = NumericProperty(1)
    density: DictProperty = DictProperty({})
    show_side_sheet: BooleanProperty = BooleanProperty(False)

    # ссылки/кэш
    _slot_nav: MDBoxLayout | None = None
    _slot_center: MDGridLayout | None = None
    _slot_side: MDBoxLayout | None = None

    _nav_rail: MDBoxLayout | None = None
    _side_sheet: MDCard | None = None
    _notif_list: MDList | None = None
    _bottom_bar: MDBoxLayout | None = None

    _cards_built: bool = False

    # throttle
    _resize_trigger = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # первичная сборка скелета
        Clock.schedule_once(self._build_once, 0)
        # throttle: не чаще, чем раз в 60 мс (≈16–20 FPS при ресайзе)
        self._resize_trigger = Clock.create_trigger(self._on_window_resized, 0.06)
        Window.bind(size=lambda *a: self._resize_trigger())

    # ---------- первичное построение скелета и кэшей ----------
    def _build_once(self, *_):
        body = self.ids.body

        # слоты: лево/центр/право
        self._slot_nav = MDBoxLayout(size_hint_x=None, width=0)
        self._slot_center = MDGridLayout(
            cols=1, spacing=(dp(16), dp(16)), size_hint=(1, 1)
        )
        self._slot_side = MDBoxLayout(size_hint_x=None, width=0)

        body.add_widget(self._slot_nav)
        body.add_widget(self._slot_center)
        body.add_widget(self._slot_side)

        # кэш нав-рейла
        self._nav_rail = Factory.NavigationRail()
        self._slot_nav.add_widget(
            self._nav_rail
        )  # добавим один раз; шириной будем управлять

        # кэш карточек (строим один раз)
        if not self._cards_built:
            for i in range(1, 7):
                card = Factory.SurfaceCard()
                card.add_widget(self._card_content(f"Карточка {i}"))
                self._slot_center.add_widget(card)
            self._cards_built = True

        # кэш side-sheet и списка уведомлений
        self._side_sheet = Factory.SideSheet()
        self._notif_list = self._notifications_list()
        self._side_sheet.add_widget(self._notif_list)
        self._slot_side.add_widget(
            self._side_sheet
        )  # всегда в дереве; шириной будем управлять

        # кэш нижней панели
        self._bottom_bar = Factory.BottomBar()
        self.add_widget(self._bottom_bar)  # всегда в дереве; высотой будем управлять

        # первичное применение раскладки
        self._on_window_resized()

    # ---------- адаптация на ресайзе (дёшево, без пересборки дерева) ----------
    def _on_window_resized(self, *_):
        w_dp = px_to_dp(Window.width)
        h_dp = px_to_dp(Window.height)

        self.width_class = classify_width(w_dp)
        self.height_class = classify_height(h_dp)

        # density → только параметры
        dens = DENSITY_COMPACT if self.height_class == "compact" else DENSITY_DEFAULT
        self.density = {
            "vgap": dens.vgap,
            "hgap": dens.hgap,
            "section_gap": dens.section_gap,
            "list_row_gap": dens.list_row_gap,
        }

        # центр: колонки и расстояния
        if self._slot_center:
            self._slot_center.cols = (
                1
                if self.width_class == "compact"
                else (2 if self.width_class == "medium" else 3)
            )
            self._slot_center.spacing = (self.density["hgap"], self.density["vgap"])

        # слева: rail шириной 0 / 72 / 96
        if self._slot_nav:
            if self.width_class == "compact":
                self._slot_nav.width = 0
            elif self.width_class == "medium":
                self._slot_nav.width = dp(72)
            else:
                self._slot_nav.width = dp(96)

        # справа: side-sheet (виден только в medium/expanded и когда пользователь включил)
        if self._slot_side:
            if self.width_class in ("medium", "expanded") and self.show_side_sheet:
                self._slot_side.width = dp(360)
            else:
                self._slot_side.width = 0

        # нижняя панель показываем только в compact
        if self._bottom_bar:
            self._bottom_bar.height = dp(64) if self.width_class == "compact" else 0

    # ---------- helpers: контент карточек ----------
    def _card_content(self, title: str):
        box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12))
        box.add_widget(self._subtitle(title))
        for j in range(3):
            row = MDBoxLayout(size_hint_y=None, height=dp(40))
            row.add_widget(self._pill(f"Элемент {j+1}"))
            box.add_widget(row)
        return box

    def _subtitle(self, text: str):
        from kivymd.uix.label import MDLabel

        bar = MDBoxLayout(size_hint_y=None, height=dp(28))
        bar.add_widget(MDLabel(text=text, font_style="Title", role="medium"))
        return bar

    def _pill(self, text: str):
        from kivymd.uix.label import MDLabel

        card = MDCard(
            radius=[dp(12)],
            padding=dp(8),
            md_bg_color=MDApp.get_running_app().theme_cls.surfaceContainerHighColor,
            size_hint_x=1,
        )
        card.add_widget(MDLabel(text=text, font_style="Body", role="medium"))
        return card

    # ---------- уведомления ----------
    def on_show_notifications(self):
        if self.width_class == "compact":
            # modal dialog (контент уже кэширован)
            dialog = MDDialog(
                MDDialogHeadlineText(text="Уведомления"),
                MDDialogContentContainer(
                    self._notifications_list(), orientation="vertical"
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="Закрыть"),
                        style="text",
                        on_release=lambda *_: dialog.dismiss(),
                    ),
                    spacing="8dp",
                ),
            )
            dialog.open()
        else:
            # toggle side-sheet; сам sheet и список уже в дереве, меняем только ширину слота
            self.show_side_sheet = not self.show_side_sheet
            self._on_window_resized()

    def _notifications_list(self):
        # если уже построен кэш — возвращаем его
        if self._notif_list:
            return self._notif_list
        lst = MDList(spacing=self.density.get("list_row_gap", dp(8)))
        for i in range(1, 10):
            item = MDListItem(divider=True)
            item.add_widget(MDListItemHeadlineText(text=f"Сообщение #{i}", bold=True))
            item.add_widget(MDListItemSupportingText(text="Короткое описание события"))
            lst.add_widget(item)
        return lst


# -------------------- App --------------------


class App(MDApp):
    def build(self):
        self.title = "MD3 ResponsiveLayout (KivyMD 2.0)"
        self.theme_cls.primary_palette = "Blue"
        Builder.load_string(KV)
        return Factory.ResponsiveRoot()


if __name__ == "__main__":
    App().run()
