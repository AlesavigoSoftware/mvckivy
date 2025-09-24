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
    # Родитель: width через РОДИТЕЛЬСКИЙ алиас (size_alias)
    # Это правило сработает на этапе применения <BaseBox>
    width: int(self.size_alias[0])
    size_hint_x: None
    size_hint_y: None
    height: 80

<ChildBox>:
    # Подкласс: ПОВЕРХ родителя переопределяем width через ДЕТСКИЙ алиас (child_alias)
    # Так мы явно используем новый алиас вместо родительского
    

<Root>:
    orientation: "vertical"
    padding: 10
    spacing: 10

    LabelBox:
        # НЕСТРОГИЙ экземпляр: width берётся из child_alias (по правилу <ChildBox>)
        ChildBox:
            id: non_strict
            alias_tag: "non_strict"
            width: int(self.child_alias[1])

        # СТРОГИЙ экземпляр: перебиваем на месте — без ребинда (-width)
        ChildBox:
            id: strict
            alias_tag: "strict"
            -width: int(self.child_alias[1])
"""


class Root(BoxLayout):
    pass


class BaseBox(BoxLayout):
    alias_tag = StringProperty("")  # для читабельных логов
    custom_size = ListProperty([])

    # Родительский алиас: size_alias
    def _get_size_alias(self):
        tag = self.alias_tag or self.__class__.__name__
        log.info(
            f"🟠 PARENT getter size_alias → {self.__class__.__name__}<{tag}> "
            f"{self.size = }, {self.custom_size = }"
        )
        return self.size if not self.custom_size else self.custom_size

    size_alias = AliasProperty(
        _get_size_alias,
        None,
        bind=["size", "custom_size"],
        cache=True,
        watch_before_use=False,
    )


class ChildBox(BaseBox):
    # Дочерний алиас: child_alias (поверх родительского)
    def _get_child_alias(self):
        tag = self.alias_tag or self.__class__.__name__
        log.info(
            f"🟢 CHILD  getter child_alias → {self.__class__.__name__}<{tag}> "
            f"{self.size = }, {self.custom_size = }"
        )
        return self.custom_size if self.custom_size else self.size

    child_alias = AliasProperty(
        _get_child_alias,
        None,
        bind=["size", "custom_size"],
        cache=True,
        watch_before_use=False,
    )


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        root = Root()
        Clock.schedule_once(lambda dt: self._after_build(root), 0)
        return root

    def _after_build(self, root):
        log.info("=== 1) Меняем size у НЕСТРОГОГО ===")
        root.ids.non_strict.size = (300, 80)
        root.ids.non_strict.custom_size = (150, 70)

        log.info("=== 2) Меняем size у СТРОГОГО ===")
        root.ids.strict.size = (400, 80)
        root.ids.strict.custom_size = (180, 70)

        log.info("=== Готово ===")


if __name__ == "__main__":
    DemoApp().run()
