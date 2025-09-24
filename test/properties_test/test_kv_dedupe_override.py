from __future__ import annotations

import logging
import unittest
from textwrap import dedent
from mvckivy.app import MKVApp
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.metrics import dp

from mvckivy.properties.dedupe_mixin import KVDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty


class Parent(KVDedupeMixin, BoxLayout):
    """Базовый класс с динамикой padding ← ui_scale."""

    ui_scale = NumericProperty(1.0)
    __kv_dedupe_targets__ = ("padding",)  # будем дедупить padding
    __kv_keep_latest__ = True  # у Parent оставляем последний биндинг

    def _get_alias_padding(self, ext: ExtendedAliasProperty):
        v = dp(8) * self.ui_scale
        return v, v, v, v

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding,
        None,
        bind=("ui_scale",),
        cache=False,
        watch_before_use=True,
    )


class Child(Parent):
    """Подкласс, в KV у которого padding: GP10 (константа)."""

    # У Child снимаем все KV-наблюдатели, чтобы константа сохранилась.
    __kv_keep_latest__ = False


KV_SRC = dedent(
    """
#:import dp kivy.metrics.dp
#:set GP10 (dp(10), dp(10), dp(10), dp(10))

<Parent>:
    # Раннее правило (динамика от ui_scale)
    padding: self.alias_padding

<Child>:
    # Позднее правило (константа)
    padding: GP10

Root:
    child: child
    parent_ref: parent
    Child:
        id: child
        ui_scale: 3.0
    Parent:
        id: parent
        ui_scale: 3.0
"""
)


class Root(BoxLayout):
    child = ObjectProperty()
    parent_ref = ObjectProperty()


class TestApp(MKVApp):
    def build(self):
        # По требованию: возвращаем результат Builder.load_string
        return Builder.load_string(KV_SRC)


# -----------------------------------------------------------------------------
# Набор 1: БЕЗ дедупа (baseline) — отражает текущее поведение из твоих логов.
# Здесь Child следует за ui_scale (24.0 при 3.0; 40.0 при 5.0).
# -----------------------------------------------------------------------------
class TestWithoutDedupe(unittest.TestCase):
    """Фиксируем текущее поведение (если дедуп не сработал/не настроен)."""

    @classmethod
    def setUpClass(cls):
        cls.app = TestApp()
        cls.app._run_prepare()
        for _ in range(6):
            Clock.tick()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.stop()
        except Exception:
            pass

    def test_child_follows_ui_scale_baseline(self):
        root: Root = self.app.root
        child: Parent = root.child
        parent: Parent = root.parent_ref

        # При ui_scale=3.0 ожидаем alias у обоих (24.0)
        self.assertEqual([dp(8) * 3.0] * 4, list(child.padding))
        self.assertEqual([dp(8) * 3.0] * 4, list(parent.padding))

        # Увеличиваем ui_scale и убеждаемся, что Child тоже сменился (40.0)
        child.ui_scale = 5.0
        parent.ui_scale = 5.0
        for _ in range(4):
            Clock.tick()

        self.assertEqual([dp(8) * 5.0] * 4, list(child.padding))
        self.assertEqual([dp(8) * 5.0] * 4, list(parent.padding))


# -----------------------------------------------------------------------------
# Набор 2: С дедупом (желаемое поведение) — Child на GP10 всегда.
# Эти тесты должны быть зелёными, когда KVDedupeMixin корректно удаляет
# ранний KV-биндинг padding из <Parent> для экземпляров Child.
# -----------------------------------------------------------------------------
class TestWithDedupe(unittest.TestCase):
    """Желаемое поведение при корректно работающем дедупе."""

    @classmethod
    def setUpClass(cls):
        cls.app = TestApp()
        cls.app._run_prepare()
        for _ in range(6):
            Clock.tick()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.stop()
        except Exception:
            pass

    def test_child_override_constant_wins(self):
        root: Root = self.app.root
        child: Parent = root.child
        parent: Parent = root.parent_ref

        logging.info(f"Parent: {parent.get_property_observers('padding')}")
        logging.info(f"Child: {child.get_property_observers('padding')}")

        # Child должен держать константу GP10 (10.0)
        self.assertEqual([dp(10)] * 4, list(child.padding))
        # Parent — динамика от ui_scale
        self.assertEqual([dp(8) * parent.ui_scale] * 4, list(parent.padding))

    def test_ui_scale_changes_affect_parent_not_child(self):
        root: Root = self.app.root
        child: Parent = root.child
        parent: Parent = root.parent_ref

        child.ui_scale = 5.0
        parent.ui_scale = 5.0
        for _ in range(4):
            Clock.tick()

        # Child остаётся на GP10
        self.assertEqual(
            [dp(10)] * 4,
            list(child.padding),
            "Ожидается, что после дедупа KV константа у Child не меняется.",
        )

        # Parent пересчитался
        self.assertEqual([dp(8) * 5.0] * 4, list(parent.padding))

    def test_parent_dynamic_alias_reacts(self):
        root: Root = self.app.root
        parent: Parent = root.parent_ref

        parent.ui_scale = 2.25
        for _ in range(3):
            Clock.tick()

        self.assertEqual([dp(8) * 2.25] * 4, list(parent.padding))


if __name__ == "__main__":
    unittest.main(verbosity=2)
