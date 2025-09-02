from __future__ import annotations
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, AliasProperty
from kivy.uix.boxlayout import BoxLayout

logging.basicConfig(level=logging.INFO, format="%(message)s")


class Probe(BoxLayout):
    value = NumericProperty(0)

    calls_arg = NumericProperty(0)
    calls_noarg = NumericProperty(0)
    calls_alias = NumericProperty(0)

    # 1) Метод с property, переданным ЯВНО как аргумент из KV
    def fmt_with_arg(self, v: int) -> str:
        self.calls_arg += 1
        logging.info(f"fmt_with_arg(v={v}) -> calls={self.calls_arg}")
        return f"[with arg] value={v} | calls={self.calls_arg}"

    # 2) Метод без аргумента (читает self.value внутри) — KV НЕ видит зависимость
    def fmt_no_arg(self) -> str:
        self.calls_noarg += 1
        logging.info(f"fmt_no_arg(value={self.value}) -> calls={self.calls_noarg}")
        return f"[no arg] value={self.value} | calls={self.calls_noarg}"

    # 3) Для сравнения: вычисляемое свойство с bind=('value',)
    def _get_alias_text(self) -> str:
        self.calls_alias += 1
        logging.info(f"alias_text(value={self.value}) -> calls={self.calls_alias}")
        return f"[alias] value={self.value} | calls={self.calls_alias}"

    alias_text = AliasProperty(_get_alias_text, None, bind=("value",))


class TestApp(App):
    def build(self):
        return Builder.load_file("probe.kv")


if __name__ == "__main__":
    TestApp().run()
