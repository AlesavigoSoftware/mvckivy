from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import NumericProperty
from kivymd.app import MDApp


class DemoApp(MDApp):
    base_height_dp = 88  # эталон для вертикального расчёта

    min_scale = NumericProperty(0.5)  # только даунскейл, чтобы не блюрило
    max_scale = NumericProperty(1.0)

    def build(self):
        self.theme_cls.primary_palette = "Olive"
        return Builder.load_file("textfield.kv")

    def on_start(self):
        Window.bind(size=self._on_resize)
        self._on_resize()

    def _on_resize(self, *_):
        """Считаем масштаб из высоты окна (можно и из min(sx, sy) — тут важна Y)."""
        stw = self.root.ids.stw
        margin = 64
        sy = (Window.height - margin) / self.base_height_dp
        scale = max(self.min_scale, min(self.max_scale, sy))
        stw.scale = scale
        # ширина управляется самим ScaledTextWidth.width — тут не трогаем


if __name__ == "__main__":
    DemoApp().run()
    # DemoApp().run_test()  # для тестов в kivyMD
