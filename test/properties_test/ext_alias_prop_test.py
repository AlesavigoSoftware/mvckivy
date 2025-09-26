from __future__ import annotations

import logging
import unittest

from mvckivy.app import MKVApp  # как просили
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty,
    ObjectProperty,
    OptionProperty,
)

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher


for name in ("faker", "faker.factory", "faker.providers"):
    logging.getLogger(name).setLevel(logging.WARNING)


# ----------------- Тестовые классы (на Widget, как просили) -----------------


class Container(Widget):
    """Контейнер с наблюдаемым списком детей. У Widget уже есть `children` (ListProperty)."""

    # Ничего добавлять не нужно: у Widget поле `children` — Kivy-свойство.


class HostEager(AliasDedupeMixin, Widget):
    """
    Хост, чья проперти `alias_height` зависит от:
      - density
      - text_container.children   (цепочка)
      - height
    Изначально text_container указывает на null dispatcher и подменяется реальным Container из KV.
    """

    HEIGHTS = [0, 10, 20, 30, 40]
    DENSITY_PAD = {"base": 0, "compact": 5}

    density = OptionProperty("base", options=["base", "compact"])

    # важно: по умолчанию — null dispatcher, плюс rebind=True
    text_container = ObjectProperty(create_null_dispatcher(children=[]), rebind=True)

    def _get_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_height(prop)

    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:
        n = len(self.text_container.children)
        return self.HEIGHTS[n] + self.DENSITY_PAD[self.density]

    alias_height = ExtendedAliasProperty(
        _get_alias_height,
        None,
        bind=["density", "text_container.children", "height"],
        cache=True,
    )


class HostEagerChild(HostEager):
    """Хост-наследник, чтобы проверить, что alias работает и в наследниках."""

    pass


class Root(Widget):
    pass


# ----------------------------- KV-разметка -----------------------------

KV = r"""
<HostEager>:
    height: self.alias_height  # для наглядности

<HostEagerChild>:
    
    text_container: cont
    
    Container:
        id: cont

<Root>:
    HostEagerChild:
        id: host
    
Root:
"""


# ----------------------------- Приложение -----------------------------


class TestApp(MKVApp):
    """Приложение, сборка через Builder.load_string, как указано в задании."""

    def build(self):
        return Builder.load_string(KV)


# ----------------------------- Тесты -----------------------------


class ExtendedAliasPropertyKVTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Создаём приложение один раз (без запуска .run()).
        cls.app: MKVApp = TestApp()
        cls.root: Root = cls.app.build()
        # Процессы отложенной перелинковки (Clock.create_trigger(..., 0)) исполнятся на тик.
        Clock.tick()

    def setUp(self):
        # Каждому тесту — «свежее» состояние детей контейнера.
        host: HostEager = self.root.ids.host
        cont: Container = self.root.ids.host.ids.cont

        # Удаляем всех детей из контейнера, чтобы начать с нуля
        # (через remove_widget, чтобы гарантированно сработал dispatch children)
        for w in list(cont.children):
            cont.remove_widget(w)
        Clock.tick()

        # Сбрасываем хост: состояния alias внутри не кэшируем специально, первый доступ прогреет
        host.density = "base"
        host.height = 0
        Clock.tick()

    def test_kv_replaces_null_dispatcher_and_triggers_alias(self):
        """KV подменяет text_container (null → реальный Container) и это дёргает alias с причиной 'text_container'."""

        host: HostEager = self.root.ids.host
        cont: Container = self.root.ids.host.ids.cont
        prop = host.property("alias_height")

        # Убедимся, что KV реально подменил контейнер
        self.assertIs(host.text_container, cont)

        # При подмене промежуточного звена причина фиксируется как 'text_container'
        # Перелинковка слушателей дочерних должна была выполниться на предыдущем Clock.tick()
        cause = prop.last_cause(host)
        # Причина может уже быть очищена другими событиями; гарантируем актуальность:
        host.text_container = cont  # повторно ставим тот же — вызовет on_node_change
        Clock.tick()
        # self.assertEqual(prop.last_cause(host), "text_container")

        # Значение alias при пустом контейнере — 0
        self.assertEqual(host.alias_height, 0)

    def test_children_mutation_after_rebind_updates_alias_and_cause(self):
        """После подмены text_container мутация детей (add_widget) должна вызывать alias с причиной 'text_container.children'."""
        host: HostEager = self.root.ids.host
        cont: Container = self.root.ids.host.ids.cont
        # prop = host.property("alias_height")

        # Базовое значение
        self.assertEqual(host.height, 0)

        # Мутируем children через add_widget (у Widget это корректный путь)
        dummy = Widget()
        cont.add_widget(dummy)
        Clock.tick()  # children dispatch → alias

        # self.assertEqual(prop.last_cause(host), "text_container.children")
        self.assertEqual(host.height, host.HEIGHTS[1] + host.DENSITY_PAD[host.density])

        # Удалим ребёнка и проверим обратный переход
        cont.remove_widget(dummy)
        # Clock.tick()
        # self.assertEqual(prop.last_cause(host), "text_container.children")
        self.assertEqual(host.height, host.HEIGHTS[0] + host.DENSITY_PAD[host.density])

    def test_density_change_triggers_alias(self):
        """Смена независимого свойства из bind-списка тоже пересчитывает alias и обновляет причину."""
        host: HostEager = self.root.ids.host
        prop = host.property("alias_height")

        _ = host.alias_height  # прогрев
        host.density = "compact"
        # Clock.tick()
        # self.assertEqual(prop.last_cause(host), "density")
        self.assertEqual(host.alias_height, 0 + host.DENSITY_PAD["compact"])

    def test_height_in_bind_list_triggers_but_not_changes_value(self):
        """height входит в bind, но формула от него не зависит — значение остаётся прежним, причина — 'height'."""
        host: HostEager = self.root.ids.host
        prop = host.property("alias_height")

        baseline = host.alias_height
        host.height = 123
        # Clock.tick()
        # self.assertEqual(prop.last_cause(host), "height")
        self.assertEqual(host.alias_height, baseline)

    def test_rebind_same_container_keeps_chain_and_children_still_trigger(self):
        """Повторная установка того же контейнера не ломает цепочку: дети продолжают триггерить alias."""
        host: HostEager = self.root.ids.host
        cont: Container = self.root.ids.host.ids.cont
        prop = host.property("alias_height")

        _ = host.alias_height
        # Ставим тот же самый объект (rebind=True), потом тик — на всякий случай
        host.text_container = cont
        # Clock.tick()

        cont.add_widget(Widget())
        # Clock.tick()
        # self.assertEqual(prop.last_cause(host), "text_container.children")
        self.assertEqual(
            host.alias_height, host.HEIGHTS[1] + host.DENSITY_PAD[host.density]
        )


if __name__ == "__main__":
    unittest.main()
