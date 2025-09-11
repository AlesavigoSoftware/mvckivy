from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTrailingCheckbox,
)
from kivymd.uix.scrollview import MDScrollView


KV = r"""
MDScreen:
    md_bg_color: app.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"

        MDButton:
            style: "filled"
            on_release: app.open_notifications_dialog()
            MDButtonText:
                text: "Открыть уведомления (компактный список в диалоге)"
"""


class DialogListItem(MDListItem):
    """
    Вариант list item для диалога:
    - типографика берётся из токенов темы (которые мы временно уменьшаем контекстно);
    - высота/паддинги — компактные;
    - фон и сам список прозрачные, чтобы «жили» в диалоге;
    - trailing checkbox.
    """

    def __init__(self, with_checkbox: bool = True, **kwargs):
        # прозрачный фон айтема (не «карточка», а строка в списке)
        kwargs.setdefault("md_bg_color", (0, 0, 0, 0))
        super().__init__(**kwargs)
        if with_checkbox:
            self.add_widget(MDListItemTrailingCheckbox())

    def on_kv_post(self, base_widget):
        Clock.schedule_once(self._apply_compact_density, 0)

    def _apply_compact_density(self, *_):
        # Сколько текстовых блоков у нас в text_container (заголовок + 1..2 supporting)
        try:
            lines = len(self.ids.text_container.children)
        except Exception:
            lines = 1

        # Компактные высоты (сохраняем touch-target >= 48dp)
        # Базовые MD3: 56/72/88 — здесь делаем компактнее для диалога:
        h_map = {1: dp(48), 2: dp(56), 3: dp(64)}
        self.height = h_map.get(lines, dp(48))

        # Компактные паддинги; для 3 строк чуток больше по вертикали
        tb = dp(6) if lines < 3 else dp(8)
        self.padding = (dp(12), tb, dp(12), tb)

        # Разделитель — тонкая линия цвета разделителя темы
        # Никакого сплошного фона у строки
        self.divider = "Full"
        self.theme_divider_color = "Primary"  # использует surfaceVariantColor темы


def _get_font_size(fs, style: str, role: str):
    """Безопасно получить font-size токена как число."""
    try:
        val = fs[style][role]["font-size"]
        # В разных сборках это уже число; если вдруг строка — пытаемся привести
        return float(val)
    except Exception:
        return None


def _set_font_size(fs, style: str, role: str, value):
    try:
        fs[style][role]["font-size"] = sp(value)
    except Exception:
        pass


@contextmanager
def dialog_typography_patch(app, scale: float = 0.92):
    """
    Временное уменьшение font-size некоторых токенов MD3
    без deepcopy DictProperty. Сохраняем только изменённые значения.
    """
    fs = app.theme_cls.font_styles
    targets = [
        ("Body", "large"),
        ("Body", "medium"),
        ("Label", "small"),
        ("Label", "medium"),
    ]

    backup = {}
    # применяем
    for style, role in targets:
        cur = _get_font_size(fs, style, role)
        if cur:
            backup[(style, role)] = cur
            _set_font_size(fs, style, role, cur * scale)

    try:
        yield
    finally:
        # откатываем только то, что меняли
        for (style, role), prev in backup.items():
            _set_font_size(fs, style, role, prev)


class App(MDApp):
    def build(self):
        self.title = "Dialog + Compact List (MD3, контекстная типографика)"
        # Светлый/тёмный можно переключать, прозрачность будет работать в обоих
        self.theme_cls.primary_palette = "Indigo"
        Window.softinput_mode = "below_target"
        return Builder.load_string(KV)

    def open_notifications_dialog(self):
        # Демо-данные (3 строки каждая)
        data = [
            {
                "title": "Соединение закрыто",
                "subtitle": "Соединение с БПЛА #1 закрыто",
                "meta": "15:45:48",
                "checked": False,
            },
            {
                "title": "Низкий заряд",
                "subtitle": "Уровень заряда < 15%",
                "meta": "15:44:02",
                "checked": True,
            },
            {
                "title": "GPS восстановлен",
                "subtitle": "Качество сигнала нормализовано",
                "meta": "15:43:10",
                "checked": False,
            },
            {
                "title": "Пакет телеметрии потерян",
                "subtitle": "Проверьте связь по LTE/RF",
                "meta": "15:42:58",
                "checked": False,
            },
            {
                "title": "Миссия приостановлена",
                "subtitle": "Ожидание команды оператора",
                "meta": "15:41:20",
                "checked": True,
            },
        ]

        # --- Контент диалога: прозрачный ScrollView + прозрачный MDList ---
        scroll = MDScrollView(
            do_scroll_x=False,
            size_hint_y=None,
            height=dp(360),
        )
        # Прозрачный контейнер списка
        mlist = MDList()
        # На некоторых темах пригодится принудительная "прозрачность" через canvas:
        mlist.md_bg_color = (0, 0, 0, 0)
        scroll.add_widget(mlist)

        # Контейнер для MDDialogContentContainer
        content = MDBoxLayout(orientation="vertical", padding=dp(4), spacing=0)
        content.md_bg_color = (0, 0, 0, 0)
        content.add_widget(scroll)

        # Диалог
        dlg = MDDialog(
            MDDialogHeadlineText(text="Уведомления", halign="left"),
            MDDialogContentContainer(content, orientation="vertical"),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Закрыть"),
                    style="text",
                    on_release=lambda *_: dlg.dismiss(),
                ),
                spacing="8dp",
            ),
        )
        dlg.size_hint = (0.92, None)
        dlg.height = dp(520)

        # Патчим типографику ТОЛЬКО на время показа диалога
        with dialog_typography_patch(self, scale=0.92):
            # наполняем список уже с уменьшенными токенами
            for it in data:
                li = DialogListItem(with_checkbox=True)
                # заголовок (Body/large по токенам KivyMD 2.0)
                li.add_widget(MDListItemHeadlineText(text=it["title"]))
                # поддерживающий текст — Label/small (два блока)
                li.add_widget(MDListItemSupportingText(text=it["subtitle"]))
                li.add_widget(MDListItemSupportingText(text=it["meta"]))
                # проставим состояние чекбокса, если нужно
                try:
                    li.children[0].active = bool(it.get("checked"))
                except Exception:
                    pass
                mlist.add_widget(li)

            dlg.open()

        # Автопрокрутка к последнему элементу (опционально)
        Clock.schedule_once(lambda *_: self._scroll_to_bottom(scroll), 0.05)

    @staticmethod
    def _scroll_to_bottom(scroll: MDScrollView):
        try:
            scroll.scroll_y = 0
        except Exception:
            pass


if __name__ == "__main__":
    App().run()
