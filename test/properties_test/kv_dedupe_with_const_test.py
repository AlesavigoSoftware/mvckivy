from __future__ import annotations

import logging
from typing import Tuple
import unittest

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout

from mvckivy.app import MKVApp as _BaseApp
from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty

for name in ("faker", "faker.factory", "faker.providers"):
    logging.getLogger(name).setLevel(logging.WARNING)


# ===== ВСПОМОГАТЕЛЬНОЕ: простая прокрутка Clock =====
def pump_frames(n: int = 3) -> None:
    for _ in range(n):
        Clock.tick()


# ====== БАЗОВЫЙ ПРОСТОЙ App ======
class SimpleKVApp(_BaseApp):
    def __init__(self, kv: str, **kwargs):
        super().__init__(**kwargs)
        self._kv = kv

    def build(self):
        return Builder.load_string(self._kv)


# ====== ОБЩИЕ БАЗОВЫЕ КЛАССЫ ДЛЯ ТЕСТОВ ======
class _BaseParent(AliasDedupeMixin, BoxLayout):
    """Общий Parent: padding/spacing считаются от ui_scale через алиасы."""

    ui_scale = NumericProperty(1.0)

    # alias_padding ← ui_scale
    def _get_alias_padding(self, prop):
        v = dp(8) * self.ui_scale
        return v, v, v, v

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding, None, bind=("ui_scale",), cache=False
    )

    # alias_spacing ← ui_scale (для мульти-целей)
    def _get_alias_spacing(self, prop):
        return dp(4) * self.ui_scale

    alias_spacing = ExtendedAliasProperty(
        _get_alias_spacing, None, bind=("ui_scale",), cache=False
    )


# ====== ТЕСТЫ ======
class TestPreferChildDefault(unittest.TestCase):
    """Режим по умолчанию: prefer_child — не трогать единственный родительский бинд,
    снимать только дубликаты (если появится override)."""

    def setUp(self):
        class Parent(_BaseParent):
            pass

        kv = r"""
<Parent>:
    padding:
        self.alias_padding
    orientation:
        "vertical"
    # Тут нет Child — проверяем, что один родительский бинд не трогается

BoxLayout:
    Parent:
        id: parent
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)
        self.parent: Parent = self.root.ids.parent  # type: ignore

    def test_parent_padding_changes_with_ui_scale(self):
        pad0 = tuple(self.parent.padding)
        self.parent.ui_scale = 2.0
        pump_frames(2)
        pad1 = tuple(self.parent.padding)
        changed = pad1 != pad0
        self.assertEqual(
            True,
            changed,
            "padding должен меняться от ui_scale в режиме prefer_child (единственный бинд не снимается)",
        )


class TestDetachAllChildOverride(unittest.TestCase):
    """Child задаёт константу padding и просит detach_all: все KV-бинды, пишущие в padding, снимаются только для Child."""

    def setUp(self):
        class Parent(_BaseParent):
            pass

        class Child(Parent):
            pass

        kv = r"""
#:import dp kivy.metrics.dp
#:set GP10 (dp(10), dp(10), dp(10), dp(10))

<Parent>
    padding:
        self.alias_padding
    orientation:
        "vertical"

<Child>
    padding: GP10

BoxLayout:
    Parent:
        id: parent
    Child:
        id: child
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)
        self.parent: Parent = self.root.ids.parent  # type: ignore
        self.child: Child = self.root.ids.child  # type: ignore
        self.gp10: Tuple[float, float, float, float] = (dp(10), dp(10), dp(10), dp(10))

    def test_child_padding_const_parent_dynamic(self):
        # Child — должен остаться на константе GP10, даже если скейл меняется
        pad0 = tuple(self.child.padding)
        self.child.ui_scale = 3.0
        pump_frames(2)
        pad1 = tuple(self.child.padding)

        self.assertEqual(
            self.gp10, pad0, "начальный padding ребёнка должен быть GP10 в detach_all"
        )
        self.assertEqual(
            self.gp10,
            pad1,
            "после изменения ui_scale у ребёнка padding должен остаться GP10 в detach_all",
        )

        # Parent — продолжает быть динамическим
        p0 = tuple(self.parent.padding)
        self.parent.ui_scale = 1.75
        pump_frames(2)
        p1 = tuple(self.parent.padding)
        self.assertEqual(
            True,
            p1 != p0,
            "родитель в detach_all ребёнка должен оставаться динамическим",
        )


class TestMultiTargets_ChildOverridesOnlyOne(unittest.TestCase):
    """У родителя несколько целей (padding, spacing), ребёнок переопределяет только padding.
    Ожидаем: padding у ребёнка — константа, spacing — остаётся динамическим от ui_scale.
    """

    def setUp(self):
        class Parent(_BaseParent):
            pass

        class Child(Parent):
            pass

        kv = r"""
#:import dp kivy.metrics.dp
#:set GP10 (dp(10), dp(10), dp(10), dp(10))

<Parent>:
    padding:
        self.alias_padding
    spacing:
        self.alias_spacing
    orientation:
        "vertical"

<Child>:
    padding: GP10
    # spacing — НЕ переопределяем, оставляем родительскую динамику

BoxLayout:
    Child:
        id: child
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)
        self.child = self.root.ids.child  # type: ignore
        self.gp10 = (dp(10), dp(10), dp(10), dp(10))

    def test_child_padding_const_spacing_dynamic(self):
        # padding — константа
        pad0 = tuple(self.child.padding)
        self.child.ui_scale = 2.2
        pump_frames(2)
        pad1 = tuple(self.child.padding)

        self.assertEqual(self.gp10, pad0, "padding должен начаться с GP10")
        self.assertEqual(
            self.gp10, pad1, "padding должен остаться GP10 после изменения ui_scale"
        )

        # spacing — динамический (должен измениться)
        sp0 = float(self.child.spacing)
        self.child.ui_scale = 3.0
        pump_frames(2)
        sp1 = float(self.child.spacing)
        self.assertEqual(
            True,
            sp1 != sp0,
            "spacing у ребёнка должен меняться (динамика от alias_spacing сохранена)",
        )


class TestKeepLatest_WithTwoSources(unittest.TestCase):
    """keep_latest: при наличии двух KV-биндов, пишущих в одну цель, остаётся самый поздний.
    Делимся источники: у родителя alias_padding ← ui_scale_p, у ребёнка alias_padding_child ← ui_scale_c.
    """

    def setUp(self):
        class ParentKL(AliasDedupeMixin, BoxLayout):
            ui_scale_p = NumericProperty(1.0)

            __kv_alias_hints__ = {"padding": ("alias_padding", "alias_padding_child")}
            __kv_default_mode__ = "prefer_child"
            __kv_log__ = False

            # родительский алиас
            def _get_alias_padding(self, prop):
                v = dp(8) * self.ui_scale_p
                return (v, v, v, v)

            def _set_alias_padding(self, _):
                return False

            alias_padding = ExtendedAliasProperty(
                _get_alias_padding,
                _set_alias_padding,
                bind=("ui_scale_p",),
                cache=False,
            )

        class ChildKL(ParentKL):
            ui_scale_c = NumericProperty(1.0)
            __kv_policy__ = {"padding": "keep_latest"}  # оставлять самый поздний

            # детский алиас
            def _get_alias_padding_child(self, prop):
                v = dp(12) * self.ui_scale_c
                return (v, v, v, v)

            def _set_alias_padding_child(self, _):
                return False

            alias_padding_child = ExtendedAliasProperty(
                _get_alias_padding_child,
                _set_alias_padding_child,
                bind=("ui_scale_c",),
                cache=False,
            )

        kv = r"""
<ParentKL>:
    padding: self.alias_padding
    orientation: "vertical"

<ChildKL>:
    # ВАЖНО: позднее правило — источник ребёнка
    padding: self.alias_padding_child

BoxLayout:
    ParentKL:
        id: parent
    ChildKL:
        id: child
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)
        self.parent = self.root.ids.parent  # type: ignore
        self.child = self.root.ids.child  # type: ignore

    def test_keep_latest_child_source_wins(self):
        # Меняем скейл у родителя — padding ребёнка НЕ должен реагировать
        pad_before = tuple(self.child.padding)
        self.parent.ui_scale_p = 3.0
        pump_frames(2)
        pad_after_parent = tuple(self.child.padding)

        unaffected = pad_after_parent == pad_before
        self.assertEqual(
            True,
            unaffected,
            "padding ребёнка не должен зависеть от родительского alias при keep_latest",
        )

        # Меняем скейл у ребёнка — padding ребёнка ДОЛЖЕН измениться
        self.child.ui_scale_c = 2.0
        pump_frames(2)
        pad_after_child = tuple(self.child.padding)

        affected = pad_after_child != pad_before
        self.assertEqual(
            True,
            affected,
            "padding ребёнка должен зависеть от детского alias при keep_latest",
        )


# ====== ДОП. ТЕСТЫ: Parent-коллбэк у Child не вызывается ======


class TestNoParentCallback_DetachAll(unittest.TestCase):
    """При detach_all у Child: родительский алиас не должен вызываться для ребёнка."""

    def setUp(self):
        class ParentC(_BaseParent):
            def _get_alias_padding(self, prop):
                # считаем вызовы родительского алиаса на КАЖДОМ инстансе
                self._p_calls = getattr(self, "_p_calls", 0) + 1
                v = dp(8) * self.ui_scale
                return (v, v, v, v)

            # переопределяем property, чтобы использовать наш счётчик
            alias_padding = ExtendedAliasProperty(
                _get_alias_padding, None, bind=("ui_scale",), cache=False
            )

        class ChildC(ParentC):
            __kv_policy__ = {"padding": "detach_all"}  # полный отцеп для padding

        kv = r"""
#:import dp kivy.metrics.dp
#:set GP10 (dp(10), dp(10), dp(10), dp(10))

<ParentC>:
    padding:
        self.alias_padding
    orientation:
        "vertical"

<ChildC>:
    padding:
        GP10

BoxLayout:
    ParentC:
        id: parent
    ChildC:
        id: child
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)  # дождаться on_kv_post и дедупа
        self.parent = self.root.ids.parent  # type: ignore
        self.child = self.root.ids.child  # type: ignore

    def test_parent_alias_not_called_on_child_after_detach_all(self):
        # Сбрасываем счётчик у child после дедупа
        setattr(self.child, "_p_calls", 0)

        # Меняем зависимость родительского алиаса у ребёнка (ui_scale у ChildC)
        self.child.ui_scale = 2.5
        pump_frames(2)

        # Родительский алиас НЕ должен вызваться для ребёнка
        self.assertEqual(
            0,
            getattr(self.child, "_p_calls", 0),
            "При detach_all родительский алиас не должен вызываться на ребёнке",
        )

        # А вот у самого Parent — должен вызываться при его изменениях
        base = getattr(self.parent, "_p_calls", 0)
        self.parent.ui_scale = 2.0
        pump_frames(2)
        self.assertEqual(
            True,
            getattr(self.parent, "_p_calls", 0) > base,
            "У Parent родительский алиас должен вызываться при изменении ui_scale",
        )


class TestNoParentCallback_KeepLatest(unittest.TestCase):
    """При keep_latest у Child: родительский алиас не должен вызываться для ребёнка,
    даже если меняются зависимости родительского алиаса на ребёнке.
    """

    def setUp(self):
        class ParentKL2(AliasDedupeMixin, BoxLayout):
            ui_scale_p = NumericProperty(1.0)

            def _get_alias_padding(self, prop):
                self._p_calls = getattr(self, "_p_calls", 0) + 1
                v = dp(8) * self.ui_scale_p
                return (v, v, v, v)

            def _set_alias_padding(self, _):
                return False

            alias_padding = ExtendedAliasProperty(
                _get_alias_padding,
                None,
                bind=("ui_scale_p",),
                cache=False,
            )

        class ChildKL2(ParentKL2):
            ui_scale_c = NumericProperty(1.0)

        kv = r"""
<ParentKL2>:
    padding:
        self.alias_padding
    orientation:
        "vertical"

<ChildKL2>:
    padding:
        [self.ui_scale_c, self.ui_scale_c, self.ui_scale_c, self.ui_scale_c]

BoxLayout:
    ParentKL2:
        id: parent
    ChildKL2:
        id: child
"""
        self.app = SimpleKVApp(kv)
        self.root = self.app.build()
        pump_frames(4)
        self.parent = self.root.ids.parent  # type: ignore
        self.child = self.root.ids.child  # type: ignore

    def test_parent_alias_not_called_on_child_after_keep_latest(self):
        # Сбрасываем счётчик на ребёнке после дедупа
        setattr(self.child, "_p_calls", 0)

        # Меняем зависимость родительского алиаса, но на ребёнке (ui_scale_p у Child)
        self.child.ui_scale_p = 1.5
        pump_frames(2)

        # Родительский алиас НЕ должен вызываться у ребёнка
        self.assertEqual(
            0,
            getattr(self.child, "_p_calls", 0),
            "При keep_latest родительский алиас не должен вызываться на ребёнке",
        )

        # У родителя — вызывается
        base = getattr(self.parent, "_p_calls", 0)
        self.parent.ui_scale_p = 1.8
        pump_frames(2)
        self.assertEqual(
            True,
            getattr(self.parent, "_p_calls", 0) > base,
            "У Parent родительский алиас должен вызываться при изменении ui_scale_p",
        )

        # Итоговое значение у ребёнка по-прежнему определяется детским алиасом
        pad0 = tuple(self.child.padding)
        self.child.ui_scale_c = 2.0
        pump_frames(2)
        pad1 = tuple(self.child.padding)
        self.assertEqual(
            True,
            pad1 != pad0,
            "При keep_latest padding ребёнка должен зависеть от детского алиаса",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
