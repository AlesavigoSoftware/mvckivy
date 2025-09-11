from __future__ import annotations
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
import logging
from mvckivy.properties.base_classes import ExtendedAliasProperty


logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("cause-demo")

KV = r"""
<Probe>
    # «Будим» алиас — ширина вычисляется через него
    width: int(self.geom_alias[0])
    size_hint_y: None
    height: 80
    padding: 8
    spacing: 8

<Root>
    orientation: "vertical"
    padding: 10
    spacing: 10
    ProbeChild:
        id: a
    ProbeChild:
        id: b
        -width: 260
"""


class Root(BoxLayout):
    pass


class Probe(BoxLayout):
    tag = StringProperty("")

    # Геттер читает «причину» у самого Property: type(self).geom_alias.last_cause(self)
    def _get_geom_alias(self, prop: ExtendedAliasProperty):
        return self._calc_geom_alias(prop)

    def _calc_geom_alias(self, prop: ExtendedAliasProperty):
        pass

    # НИЧЕГО в классе не биндим — всё делает свойство
    geom_alias = ExtendedAliasProperty(
        _get_geom_alias,
        bind=["size", "x"],  # зависимости, как обычно
        cache=True,
        watch_before_use=True,
        track_components=True,  # автоматически добавит width/height, x/y
    )


class ProbeChild(Probe):
    def _calc_geom_alias(self, prop: ExtendedAliasProperty):
        # просто возвращаем кортеж (ширина, высота)
        cause = prop.last_cause(self)
        log.info(
            f"🔎 getter geom_alias: cause={cause!r} size={tuple(self.size)} pos={tuple(self.pos)}"
        )
        # любая ваша логика
        return self.size


class DemoApp(App):
    def build(self):
        Builder.load_string(KV)
        root = Root()
        Clock.schedule_once(lambda dt: self._demo(root), 0)
        return root

    def _demo(self, root):
        a, b = root.ids.a, root.ids.b
        log.info("\n=== A.size = (300, 80) ===")
        a.size = (
            300,
            80,
        )  # увидите cause: 'size.width' → затем 'size.height' (или сводное 'size')
        log.info("\n=== A.x += 40 ===")
        a.x = a.x + 40  # cause: 'pos.x' / 'pos.y' (или 'pos')
        log.info("\n=== B.size = (360, 80) ===")
        b.size = (360, 80)


if __name__ == "__main__":
    DemoApp().run()
