"""Мини-приложение для ручной проверки MKVDialog."""

from __future__ import annotations

from functools import partial
from pathlib import Path

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.factory import Factory
from kivy.uix.widget import Widget

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from mvckivy.app import MKVApp
from mvckivy.uix.dialog import (
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_DIALOG_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "dialog" / "dialog.kv"
KV_TEST_PATH = Path(__file__).with_name("main.kv")

# Зарегистрируем классы до загрузки KV
for _cls in (
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
    MDLabel,
    MDButton,
    MDButtonText,
    MDBoxLayout,
    MDTextField,
):
    Factory.register(_cls.__name__, cls=_cls)


class Root(MDBoxLayout):
    pass


class DialogDemoApp(MKVApp):
    title = "MKVDialog Demo"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_dialog: MKVDialog | None = None

    # --- lifecycle -----------------------------------------------------
    def build(self):
        if KV_DIALOG_PATH.exists():
            Builder.load_file(str(KV_DIALOG_PATH))
        Builder.load_file(str(KV_TEST_PATH))
        return Root()

    # --- dialog helpers ------------------------------------------------
    def _spawn_dialog(self) -> MKVDialog:
        if self._active_dialog is not None:
            self._active_dialog.dismiss()
        dialog = MKVDialog()
        dialog.bind(on_dismiss=partial(self._on_dialog_dismiss, dialog))
        self._active_dialog = dialog
        return dialog

    def open_basic_dialog(self) -> None:
        dialog = self._spawn_dialog()
        dialog.add_widget(MKVDialogIcon(icon="information"))
        dialog.add_widget(MKVDialogHeadlineText(text="Простой диалог"))
        dialog.add_widget(
            MKVDialogSupportingText(
                text="Использует виджеты MKVDialog*, \'подключенные\' из Python",
            )
        )

        buttons = MKVDialogButtonContainer(spacing=dp(12))
        buttons.add_widget(self._build_close_button(dialog, "Закрыть"))
        dialog.add_widget(buttons)
        dialog.open()

    def open_form_dialog(self) -> None:
        dialog = self._spawn_dialog()
        dialog.add_widget(MKVDialogIcon(icon="account"))
        dialog.add_widget(MKVDialogHeadlineText(text="Форма обратной связи"))

        content = MKVDialogContentContainer(orientation="vertical", spacing=dp(12))
        content.add_widget(
            MDLabel(
                text="Введите комментарий ниже:",
                halign="left",
                adaptive_height=True,
            )
        )
        content.add_widget(Widget(size_hint_y=None, height=dp(4)))
        comment_field = MDTextField(
            hint_text="Комментарий",
            multiline=True,
            size_hint_y=None,
            height=dp(96),
        )
        content.add_widget(comment_field)
        dialog.add_widget(content)

        buttons = MKVDialogButtonContainer(spacing=dp(12))
        buttons.add_widget(self._build_close_button(dialog, "Отмена"))
        buttons.add_widget(self._build_close_button(dialog, "Отправить"))
        dialog.add_widget(buttons)

        dialog.open()

    def _build_close_button(self, dialog: MKVDialog, text: str) -> MDButton:
        button = MDButton(style="text")
        button.add_widget(MDButtonText(text=text))
        button.bind(on_release=lambda *_: dialog.dismiss())
        return button

    def _on_dialog_dismiss(self, dialog: MKVDialog, *_):
        if self._active_dialog is dialog:
            self._active_dialog = None


if __name__ == "__main__":
    DialogDemoApp().run()
