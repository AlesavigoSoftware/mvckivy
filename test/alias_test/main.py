from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import AliasProperty, StringProperty, ListProperty
from kivy.clock import Clock
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("demo")

KV = r"""
<LabelBox@BoxLayout>:
    orientation: "vertical"
    spacing: 6
    padding: 6

<BaseBox>:
    # базовое правило ИСПОЛЬЗУЕТ алиас
    width: int(root.size_alias[0])    # <- использование алиаса
    size_hint_x: None
    size_hint_y: None
    height: 80

<ChildUses>:
    # алиас остаётся задействованным (ничего не переопределяем)

<ChildConst>:
    # переопределяем width константой — алиас больше не нужен
    width: 260
    # -width: 260

<Root>:
    orientation: "vertical"
    padding: 10
    spacing: 10

    LabelBox:
        # СЦЕНАРИЙ 1: алиас ИСПОЛЬЗУЕТСЯ
        ChildUses:
            id: uses1
            alias_tag: "uses1"
        ChildUses:
            id: uses2
            alias_tag: "uses2"

    LabelBox:
        # СЦЕНАРИЙ 2: алиас ЗАМЕНЁН константой
        ChildConst:
            id: const1
            alias_tag: "const1"
        ChildConst:
            id: const2
            alias_tag: "const2"
"""


class Root(BoxLayout):
    pass


class BaseBox(BoxLayout):
    alias_tag = StringProperty("")  # для понятной метки в логах
    custom_size = ListProperty([])

    def _get_size_alias(self):
        # покажем "чей" геттер вызван
        tag = self.alias_tag or f"{self.__class__.__name__}"
        log.info(
            f"⚡ getter size_alias → {self.__class__.__name__}<{tag}> {self.size = }, {self.custom_size = }"
        )
        return self.size if not self.custom_size else self.custom_size

    size_alias = AliasProperty(
        _get_size_alias,
        None,
        bind=["size", "custom_size"],
        cache=True,
        watch_before_use=False,
    )


class ChildUses(BaseBox):
    def _get_size_alias(self):
        # Does not work
        log.info(
            f"⚡ getter size_alias → {self.__class__.__name__} size={tuple(self.size)}"
        )
        return self.size


class ChildConst(BaseBox):
    def _get_size_alias(self):
        # Does not work
        log.info(
            f"⚡ getter size_alias → {self.__class__.__name__} size={tuple(self.size)}"
        )
        return self.size


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        root = Root()
        self.label_box = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.label_box.add_widget(BaseBox(width=260, alias_tag="BaseBox"))
        root.add_widget(self.label_box)
        Clock.schedule_once(lambda dt: self._after_build(root), 0)
        return root

    def _after_build(self, root):
        log.info("=== 1) Меняем size у ИСПОЛЬЗУЮЩИХ алиас (ChildUses) ===")
        root.ids.uses1.size = (300, 80)
        root.ids.uses2.size = (350, 80)
        root.ids.uses1.custom_size = (150, 70)
        root.ids.uses2.custom_size = (200, 70)

        log.info("=== 2) Меняем size у КОНСТАНТНЫХ (ChildConst) ===")
        root.ids.const1.size = (400, 80)
        root.ids.const2.size = (450, 80)
        root.ids.const1.custom_size = (180, 70)
        root.ids.const2.custom_size = (220, 70)

        log.info("=== 3) Явно читаем alias у каждого виджета ===")
        _ = root.ids.uses1.size_alias
        _ = root.ids.uses2.size_alias
        _ = root.ids.const1.size_alias
        _ = root.ids.const2.size_alias
        _ = self.label_box.children[0].size_alias

        log.info("=== Готово ===")


if __name__ == "__main__":
    DemoApp().run()
