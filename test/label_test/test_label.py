from __future__ import annotations

import unittest

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from mvckivy.app import MKVApp
from mvckivy.uix.label import MKVLabel, MKVIcon
from mvckivy.utils.builder import MVCBuilder


def pump_frames(count: int = 3) -> None:
    for _ in range(count):
        Clock.tick()


class _LabelTestApp(MKVApp):
    def build(self):
        return BoxLayout()


class LabelTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        MVCBuilder.load_libs_kv_files()
        cls.app = _LabelTestApp()
        cls.root = cls.app.build()
        pump_frames()

    def tearDown(self) -> None:
        self.root.clear_widgets()
        pump_frames()


class TestMKVLabel(LabelTestCase):
    def test_alias_text_size_tracks_flags(self) -> None:
        label = MKVLabel(text="Alias sizing")
        label.size_hint = (None, None)
        label.size = (320, 48)
        self.root.add_widget(label)
        pump_frames()

        self.assertEqual(label.alias_text_size, (label.width, None))
        self.assertEqual(tuple(label.text_size), (label.width, None))

        label.width = 480
        pump_frames()
        self.assertEqual(label.alias_text_size, (label.width, None))
        self.assertEqual(tuple(label.text_size), (label.width, None))

        label.adaptive_width = True
        pump_frames()
        self.assertEqual(label.alias_text_size, (None, None))
        self.assertEqual(tuple(label.text_size), (None, None))

        label.adaptive_width = False
        pump_frames()
        self.assertEqual(label.alias_text_size, (label.width, None))
        self.assertEqual(tuple(label.text_size), (label.width, None))

        label.width = 512
        pump_frames()
        self.assertEqual(label.alias_text_size, (label.width, None))
        self.assertEqual(tuple(label.text_size), (label.width, None))

        label.adaptive_size = True
        pump_frames()
        self.assertEqual(label.alias_text_size, (None, None))
        self.assertEqual(tuple(label.text_size), (None, None))

        label.adaptive_size = False
        pump_frames()
        label.width += 24
        pump_frames()
        self.assertEqual(label.alias_text_size, (label.width, None))
        self.assertEqual(tuple(label.text_size), (label.width, None))

    def test_alias_color_prefers_custom_value(self) -> None:
        label = MKVLabel(text="Color test")
        self.root.add_widget(label)
        pump_frames()

        label.theme_cls.theme_style_switch_animation = False
        label.theme_text_color = "Custom"
        custom_color = (0.25, 0.75, 0.5, 1)
        label.text_color = custom_color
        pump_frames()

        self.assertEqual(tuple(label.alias_color), custom_color)
        self.assertEqual(tuple(label.color), custom_color)

    def test_alias_color_falls_back_when_theme_values_missing(self) -> None:
        label = MKVLabel(text="Color fallback")
        self.root.add_widget(label)
        pump_frames()

        class _ThemeStub:
            def __init__(self):
                self.onSurfaceColor = (0.1, 0.2, 0.3, 1.0)

        original_theme = label.theme_cls
        label.theme_cls = _ThemeStub()
        pump_frames()

        label.theme_text_color = "Secondary"
        pump_frames()
        self.assertEqual(tuple(label.alias_color), (0.1, 0.2, 0.3, 1.0))

        label.theme_text_color = "Hint"
        pump_frames()
        self.assertEqual(tuple(label.alias_color), (0.1, 0.2, 0.3, 1.0))

        label.theme_text_color = "Error"
        pump_frames()
        self.assertEqual(tuple(label.alias_color), (0.1, 0.2, 0.3, 1.0))

        label.theme_cls = original_theme


class TestMKVIcon(LabelTestCase):
    def test_icon_source_falls_back_to_icon_text(self) -> None:
        icon = MKVIcon(icon="non_builtin_icon")
        self.root.add_widget(icon)
        pump_frames()

        icon.font_name = "Roboto"
        pump_frames()

        self.assertEqual(icon.alias_icon_source, "non_builtin_icon")
        self.assertEqual(icon.source, "non_builtin_icon")
