from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.core.text import LabelBase


class TelemetryApp(MDApp):
    altitude = NumericProperty(10.9)
    speed = NumericProperty(12.3)
    battery = NumericProperty(0.68)
    signal = NumericProperty(0.92)
    lat = NumericProperty(34.0522)
    lon = NumericProperty(-118.2437)
    flight_alt = NumericProperty(122.0)
    status_text = StringProperty("Active")
    status_ok = BooleanProperty(True)

    text_scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        LabelBase.register(
            name="nasalization",
            fn_regular=r"C:\Users\alesa\Documents\AlesavigoSoftware\agro-flow-app\src\assets\fonts\nasalization-regular-en-ru.otf",
        )

    def build(self):
        self.title = "Drone Telemetry Card"
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"

        Builder.load_file("telemetry_card.kv")
        root = Builder.load_string(
            """
MDScreen:
    md_bg_color: app.theme_cls.backgroundColor
    MDBoxLayout:
        padding: "16dp"
        TelemetryCard:
            id: card
            size_hint: None, None
            # Масштабируем по ширине и по высоте с сохранением пропорций base_w:base_h
            width: self.base_w * min(self.parent.width * 0.9 / self.base_w, self.parent.height * 0.9 / self.base_h)
            height: self.base_h * min(self.parent.width * 0.9 / self.base_w, self.parent.height * 0.9 / self.base_h)
            pos_hint: {"center_x": .5, "center_y": .5}
"""
        )
        Clock.schedule_once(self._fill, 0)
        Window.bind(size=self._on_window_resize)
        self._on_window_resize(Window, Window.size)
        return root

    def _on_window_resize(self, _window, _size):
        base_w, base_h = 360.0, 420.0
        scale_w = Window.width / base_w
        scale_h = Window.height / base_h
        self.text_scale = max(0.85, min(1.6, min(scale_w, scale_h)))

    def m3_size(self, style: str, role: str) -> float:
        table = {
            ("Display", "large"): 57,
            ("Display", "medium"): 45,
            ("Display", "small"): 36,
            ("Headline", "large"): 32,
            ("Headline", "medium"): 28,
            ("Headline", "small"): 24,
            ("Title", "large"): 22,
            ("Title", "medium"): 16,
            ("Title", "small"): 14,
            ("Body", "large"): 16,
            ("Body", "medium"): 14,
            ("Body", "small"): 12,
            ("Label", "large"): 14,
            ("Label", "medium"): 12,
            ("Label", "small"): 11,
        }
        return table.get((style, role), 14)

    def _fill(self, *_):
        ids = self.root.ids.card.ids
        ids.alt_value.text = f"{self.altitude:.1f}"
        ids.spd_value.text = f"{self.speed:.1f}"
        ids.batt_bar.value = int(self.battery * 100)
        ids.batt_pct.text = f"{int(self.battery*100)}%"
        ids.sig_bar.value = int(self.signal * 100)
        ids.sig_pct.text = f"{int(self.signal*100)}%"
        ids.lat_value.text = f"{self.lat:.4f}°"
        ids.lon_value.text = f"{self.lon:.4f}°"
        ids.flight_value.text = f"{self.flight_alt:.1f} m"
        ids.status_label.text = self.status_text
        ids.status_dot.md_bg_color = (
            (0, 0.72, 0.24, 1) if self.status_ok else (1, 0.33, 0.33, 1)
        )

    def on_change_pressed(self, *_):
        self.status_ok = not self.status_ok
        self.status_text = "Active" if self.status_ok else "Paused"
        self._fill()


if __name__ == "__main__":
    TelemetryApp().run()
