# on_kv_post_test.py
from __future__ import annotations

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

KV = r"""
#:import dp kivy.metrics.dp

<ProbeKV>:
    # Просто, чтобы отличался визуально
    canvas.before:
        Color:
            rgba: 0.3, 0.6, 0.9, 0.25
        Rectangle:
            pos: self.pos
            size: self.size

<TestRow>:
    size_hint_y: None
    height: dp(34)
    spacing: dp(8)
    Label:
        text: root.title
        size_hint_x: 0.55
        halign: 'left'
        valign: 'middle'
        text_size: self.size
    Label:
        text: root.status
        halign: 'left'
        valign: 'middle'
        text_size: self.size
"""


class Probe(Widget):
    """Создаётся ТОЛЬКО из Python (без kv-правила)."""

    called = BooleanProperty(False)
    tag = StringProperty("Probe (no kv)")

    def on_kv_post(self, base_widget):
        self.called = True
        Logger.info(
            f"KVPOST: {self.tag} -> on_kv_post(base={base_widget.__class__.__name__})"
        )


class ProbeKV(Probe):
    """Наследник с kv-правилом (см. KV выше)."""

    tag = StringProperty("ProbeKV (with kv)")


class TestRow(BoxLayout):
    title = StringProperty("")
    status = StringProperty("ожидание…")


class KvPostApp(App):
    def build(self):
        Builder.load_string(KV)

        root = BoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        # Виджеты-пробники
        self.p_no_kv = Probe()
        self.p_with_kv = ProbeKV()

        # Контейнер, чтобы они попали в дерево
        container = BoxLayout()
        container.add_widget(self.p_no_kv)
        container.add_widget(self.p_with_kv)

        # Заголовок
        root.add_widget(
            Label(
                text="[b]on_kv_post checker[/b]",
                markup=True,
                size_hint_y=None,
                height="28dp",
            )
        )

        # Строки статуса (обычные инстансы класса, не шаблоны)
        self.row_no_kv = TestRow(title="Класс без kv-правила")
        self.row_with_kv = TestRow(title="Класс с kv-правилом")
        root.add_widget(self.row_no_kv)
        root.add_widget(self.row_with_kv)

        root.add_widget(
            Label(
                text="Смотрите логи в консоли (префикс KVPOST).",
                size_hint_y=None,
                height="22dp",
            )
        )
        root.add_widget(container)

        # После построения дерева проверяем флаги
        Clock.schedule_once(self._refresh_status, 0)
        return root

    def _refresh_status(self, *_):
        self.row_no_kv.status = "ВЫЗВАН" if self.p_no_kv.called else "НЕ вызван"
        self.row_with_kv.status = "ВЫЗВАН" if self.p_with_kv.called else "НЕ вызван"
        Logger.info(
            f"RESULT: no_kv={self.p_no_kv.called}, with_kv={self.p_with_kv.called}"
        )


if __name__ == "__main__":
    KvPostApp().run()
