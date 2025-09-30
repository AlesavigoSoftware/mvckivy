"""Мини-приложение для ручной проверки MKVDialog и MDDialog.

Запуск:
    python mkv_dialog.py
"""

from __future__ import annotations

from pathlib import Path

from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from mvckivy.app import MKVApp

# --- ваш кастомный диалог ---
from mvckivy.uix.dialog import (
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
)

# --- оригинальный MDDialog для сравнения ---
# (импорты держим на модуле, чтобы классы зарегистрировались в Factory)
from kivymd.uix.dialog import (  # type: ignore
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_DIALOG_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "dialog" / "dialog.kv"
KV_TEST_PATH = Path(__file__).with_suffix(".kv")


# Хранение импорта в кортеже гарантирует, что классы зарегистрированы в Factory.
FACTORY_CLASSES = (
    # кастомные
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
    # оригинальные
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogContentContainer,
    MDDialogButtonContainer,
)


class Root(MDBoxLayout):
    pass


class DemoDialogApp(MKVApp):
    title = "MKV / MD Dialog Demo"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mkv_dialog = None
        self._md_dialog = None

    def build(self):
        if KV_DIALOG_PATH.exists():
            Builder.load_file(str(KV_DIALOG_PATH))
        root = Builder.load_file(str(KV_TEST_PATH))

        # лениво создаём оба диалога через Factory
        self._mkv_dialog = Factory.DemoDialog()
        self._md_dialog = Factory.DemoMDDialog()
        return root

    # --- MKVDialog ---
    def open_mkv_dialog(self):
        if self._mkv_dialog is None:
            self._mkv_dialog = Factory.DemoDialog()
        self._mkv_dialog.open()

    def close_mkv_dialog(self):
        if self._mkv_dialog is not None:
            self._mkv_dialog.dismiss()

    # --- MDDialog (оригинальный) ---
    def open_md_dialog(self):
        if self._md_dialog is None:
            self._md_dialog = Factory.DemoMDDialog()
        self._md_dialog.open()

    def close_md_dialog(self):
        if self._md_dialog is not None:
            self._md_dialog.dismiss()

    # --- общая «смена темы», чтобы сразу видеть разницу в обоих диалогах ---
    def toggle_theme(self):
        next_theme = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        self.theme_cls.theme_style = next_theme


if __name__ == "__main__":
    DemoDialogApp().run()
