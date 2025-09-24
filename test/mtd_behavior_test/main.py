from __future__ import annotations

import unittest

from kivy.clock import Clock
from kivy.lang import Builder

from mvckivy.app import MKVApp
from mvckivy.uix.behaviors.adaptive_behavior import (
    DeviceProfile,
)
from mvckivy.uix.layout.responsive_layout import MKVResponsiveLayout, MTDWidget


def pump_frames(n: int = 3) -> None:
    """Простая прокачка Clock, чтобы отработали schedule_once/trigger'ы."""
    for _ in range(n):
        Clock.tick()


class UITestApp(MKVApp):
    """Мини-приложение для тестов. В build() отдаем корень (Builder из строки)."""

    def __init__(self, kv: str, **kwargs):
        self._kv = kv
        super().__init__(**kwargs)

    def build(self):
        root = Builder.load_string(self._kv)
        return root


KV_BASE = r"""
#:import MTDWidget mvckivy.uix.layout.responsive_layout.MTDWidget
#:import MKVResponsiveLayout mvckivy.uix.layout.responsive_layout.MKVResponsiveLayout

# Специфичный под mobile+portrait
<MP@MTDWidget+Widget>:
    d_types: ["mobile"]
    d_orients: ["portrait"]

# Специфичный только по типу mobile (ориентация любая)
<MAny@MTDWidget+Widget>:
    d_types: ["mobile"]
    d_orients: ["*"]

# Полностью общий вариант
<Generic@MTDWidget+Widget>:
    d_types: ["*"]
    d_orients: ["*"]

# Равная специфичность, чтобы проверить "поздний побеждает"
<MAnyA@MTDWidget+Widget>:
    d_types: ["mobile"]
    d_orients: ["*"]

<MAnyB@MTDWidget+Widget>:
    d_types: ["mobile"]
    d_orients: ["*"]

# Вариант, заведомо не для текущей платформы (чтобы проверить фильтрацию при регистрации):
<AlienPlat@MTDWidget+Widget>:
    d_plat: ["zzz_nonexistent_platform"]
    d_types: ["mobile"]
    d_orients: ["portrait"]
"""


class TestMTDWidgetSBind(unittest.TestCase):
    def test_sbind_is_single_attach(self):
        w = MTDWidget()
        calls = []

        def cb(*_):
            calls.append(1)

        # дважды привязываем один и тот же колбэк
        w.sbind(size=cb)
        w.sbind(size=cb)

        # меняем размер два раза → колбэк должен вызваться ровно 2 раза (а не 4)
        w.size = (123, 45)
        w.size = (124, 46)
        pump_frames(1)
        self.assertEqual(2, len(calls))


class TestSingleInterfaceWidgetEvents(unittest.TestCase):
    def setUp(self) -> None:
        # Мини-дерево: просто сам билдер (он наследует SingleInterfaceWidget)
        kv = (
            KV_BASE
            + r"""
MKVResponsiveLayout:
    id: builder
"""
        )
        self.app = UITestApp(kv)
        self.root = self.app.build()
        pump_frames()

    def test_on_add_remove_interface_events(self):
        builder: MKVResponsiveLayout = self.root
        events = {"added": 0, "removed": 0}

        def on_add(_inst, child):
            events["added"] += 1

        def on_remove(_inst, child):
            events["removed"] += 1

        builder.bind(on_add_interface=on_add, on_remove_interface=on_remove)

        # Прямо добавим и потом удалим интерфейс (не кандидата!)
        w1 = MTDWidget()
        builder.add_widget(w1, render=True)
        pump_frames()
        self.assertEqual(1, events["added"])

        builder.clear_widgets()
        pump_frames()
        self.assertEqual(2, events["removed"])


class TestMKVResponsiveLayoutFromKV(unittest.TestCase):
    def setUp(self) -> None:
        # Корневой билдер + кандидаты через KV
        kv = (
            KV_BASE
            + r"""
MKVResponsiveLayout:
    id: builder
    # Регистрируем кандидатов (без render) — MKVResponsiveLayout.add_widget перехватит и НЕ добавит в children.
    Generic:
    MAny:
    MP:
"""
        )
        self.app = UITestApp(kv)
        self.root: MKVResponsiveLayout = self.app.build()
        pump_frames()

    def test_candidates_registered_and_best_selected(self):
        builder: MKVResponsiveLayout = self.root

        # Первичное переключение: руками шлём профиль (на реальных событиях это сделает ваш MTDBehavior)
        builder.on_profile(
            DeviceProfile(device_type="mobile", device_orientation="portrait")
        )
        pump_frames()

        # Должен быть выбран наиболее специфичный вариант: класс MP
        current = builder._interface
        self.assertIsNotNone(current)
        self.assertEqual(current.__class__.__name__, "MP")

        # Перебросим в mobile+landscape — останется MAny (т.к. портретный MP больше не подходит)
        builder.on_profile(
            DeviceProfile(device_type="mobile", device_orientation="landscape")
        )
        pump_frames()
        self.assertEqual(builder._interface.__class__.__name__, "MAny")

        # Перебросим в desktop — останется Generic
        builder.on_profile(
            DeviceProfile(device_type="desktop", device_orientation="landscape")
        )
        pump_frames()
        self.assertEqual(builder._interface.__class__.__name__, "Generic")

    def test_platform_filtered_candidate_not_registered(self):
        # Поднимем другой билд, где среди кандидатов есть «чужая» платформа
        kv = (
            KV_BASE
            + r"""
MKVResponsiveLayout:
    id: builder
    Generic:
    AlienPlat:   # d_plat = ["zzz_nonexistent_platform"] -> будет отфильтрован при регистрации
    MP:
"""
        )
        app = UITestApp(kv)
        root: MKVResponsiveLayout = app.build()
        pump_frames()

        # Пробуем выбрать mobile+portrait: доступен MP (платформа «чужого» варианта отфильтрована)
        root.on_profile(
            DeviceProfile(device_type="mobile", device_orientation="portrait")
        )
        pump_frames()
        self.assertEqual(root._interface.__class__.__name__, "MP")

    def test_fallback_when_no_variant(self):
        # Если ни один кандидат не подходит — должен подставиться пустой MTDWidget
        kv = (
            KV_BASE
            + r"""
MKVResponsiveLayout:
    id: builder
    # Заведомо неподходящие кандидаты для desktop+portrait
    MAny:
    MP:
"""
        )
        app = UITestApp(kv)
        root: MKVResponsiveLayout = app.build()
        pump_frames()

        root.on_profile(
            DeviceProfile(device_type="desktop", device_orientation="portrait")
        )
        pump_frames()

        self.assertIsNotNone(root._interface)
        # Фолбэк создаётся как базовый MTDWidget (не одна из наших динамических KV-классов)
        self.assertEqual(root._interface.__class__, MTDWidget)


class TestTieBreakRegistrationOrder(unittest.TestCase):
    def setUp(self) -> None:
        # Два варианта равной специфичности (mobile+*), второй объявлен ПОЗЖЕ → должен выигрывать
        kv = (
            KV_BASE
            + r"""
MKVResponsiveLayout:
    id: builder
    Generic:
    MAnyA:
    MAnyB:
"""
        )
        self.app = UITestApp(kv)
        self.root: MKVResponsiveLayout = self.app.build()
        pump_frames()

    def test_late_registration_wins_on_equal_specificity(self):
        self.root.on_profile(
            DeviceProfile(device_type="mobile", device_orientation="portrait")
        )
        pump_frames()
        # При равной специфичности должен победить более поздний (MAnyB)
        self.assertEqual(self.root._interface.__class__.__name__, "MAnyB")


if __name__ == "__main__":
    unittest.main()
