from __future__ import annotations

from kivy.animation import Animation
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.button import MDIconButton
from kivymd.app import MDApp

from mvckivy.properties.null_dispatcher import create_null_dispatcher


class SpeedDialAction(MDIconButton):
    """Элемент-экшен SpeedDial. Имеет порядок появления (order)."""

    order = NumericProperty(0)
    sd: ObjectProperty[SpeedDial | None] = ObjectProperty(
        create_null_dispatcher(
            main_x=0,
            main_y=0,
            main_size=0,
            animation_progress=0,
            action_size=0,
            spacing=0,
            stack_direction="down",
        ),
        rebind=True,
        allownone=False,
    )

    def _get_alias(self) -> float:
        return self._calc_alias()

    def _calc_alias(self) -> float:
        sd = self.sd
        if sd is None:
            return 0.0
        return sd.animation_progress

    alias = AliasProperty(
        _get_alias, None, bind=["sd"], cache=True, watch_before_use=True
    )


class AnotherAction(SpeedDialAction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.alias = 0.1


class SpeedDial(FloatLayout):
    """
    Прозрачный SpeedDial: одна главная кнопка-тогглер и набор action-кнопок,
    которые «вырастают» и смещаются из главной при раскрытии.
    """

    # --- публичные проперти для управления из KV/кода ---
    expanded = BooleanProperty(True)
    animation_progress = NumericProperty(1.0)  # 0..1 — читает KV
    animation_duration = NumericProperty(0.22)

    main_size = NumericProperty(dp(64))  # размер главной
    action_size = NumericProperty(dp(56))  # размер экшенов
    spacing = NumericProperty(dp(12))  # расстояние между экшенами
    edge_padding = NumericProperty(dp(16))
    anchor_x = OptionProperty("right", options=["left", "right"])
    anchor_y = OptionProperty("center", options=["top", "center", "bottom"])
    stack_direction = OptionProperty(
        "down", options=["up", "down"]
    )  # куда «уезжают» экшены

    root_icon = StringProperty("plus")
    actions_content = ObjectProperty(None, rebind=True)  # контейнер из KV

    # --- вычислимые: позиция главной кнопки (нижний-левый угол) ---
    def _get_main_x(self) -> float:
        if self.anchor_x == "left":
            return self.x + float(self.edge_padding)
        return self.right - float(self.edge_padding) - float(self.main_size)

    def _get_main_y(self) -> float:
        if self.anchor_y == "bottom":
            return self.y + float(self.edge_padding)
        if self.anchor_y == "top":
            return self.top - float(self.edge_padding) - float(self.main_size)
        # center
        return self.center_y - float(self.main_size) / 2.0

    main_x = AliasProperty(
        _get_main_x, None, bind=("x", "right", "edge_padding", "main_size", "anchor_x")
    )
    main_y = AliasProperty(
        _get_main_y,
        None,
        bind=("y", "top", "center_y", "edge_padding", "main_size", "anchor_y"),
    )

    # --- API ---
    def toggle(self) -> None:
        self.expanded = not self.expanded

    # --- internal helpers ---
    def _reindex_actions(self) -> None:
        """Пронумеровать экшены по порядку появления (0,1,2,...)."""
        ac = self.actions_content
        if not ac:
            return
        # хотим «сверху вниз» визуально одинаковый шаг; используем обратный порядок children
        for i, w in enumerate(reversed(ac.children)):
            if isinstance(w, SpeedDialAction):
                w.order = i

    # --- lifecycle / bindings ---
    def on_kv_post(self, *_):
        # вставить контейнер внутрь (поверх FloatLayout)
        ac = self.actions_content
        if ac is not None and ac.parent is not self:
            if ac.parent is not None:
                ac.parent.remove_widget(ac)
            # кладём в иерархию, но сам контейнер нулевого размера — все дети позиционируются сами
            self.add_widget(ac)

        # следить за изменением набора детей в контейнере
        if ac is not None:
            ac.fbind("children", lambda *_: self._reindex_actions())
        self._reindex_actions()

        # инициализировать прогресс
        self.animation_progress = 1.0 if self.expanded else 0.0

    def on_actions_content(self, *_):
        # если контейнер поменяли после инициализации
        self.on_kv_post()

    def on_expanded(self, *_):
        Animation.cancel_all(self, "animation_progress")
        Animation(
            animation_progress=1.0 if self.expanded else 0.0,
            d=float(self.animation_duration),
            t="out_cubic",
        ).start(self)


# ---------------- demo ----------------
class DemoApp(MDApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Aliceblue"
        return Builder.load_file("speeddial.kv")

    # callbacks
    def on_add_point(self):
        print("Add point")

    def on_download(self):
        print("Download")

    def on_stats(self):
        print("Statistics")

    def on_edit(self):
        print("Edit")


if __name__ == "__main__":
    DemoApp().run()
