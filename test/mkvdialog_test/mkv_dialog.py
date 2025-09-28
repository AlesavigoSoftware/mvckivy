"""Мини-приложение для ручной проверки MKVDialog.

Запуск:
    python mkv_dialog.py
"""

from __future__ import annotations

from pathlib import Path

from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout

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
KV_TEST_PATH = Path(__file__).with_suffix(".kv")

# Хранение импорта в кортеже гарантирует, что классы зарегистрированы в Factory.
FACTORY_CLASSES = (
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
)


class Root(MDBoxLayout):
    pass


class DemoDialogApp(MKVApp):
    title = "MKV Dialog Demo"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dialog = None

    def build(self):
        if KV_DIALOG_PATH.exists():
            Builder.load_file(str(KV_DIALOG_PATH))
        root = Builder.load_file(str(KV_TEST_PATH))
        self._dialog = Factory.DemoDialog()
        return root

    def open_dialog(self):
        if self._dialog is None:
            self._dialog = Factory.DemoDialog()
        self._dialog.open()

    def close_dialog(self):
        if self._dialog is not None:
            self._dialog.dismiss()

    def toggle_theme(self):
        next_theme = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        self.theme_cls.theme_style = next_theme


if __name__ == "__main__":
    DemoDialogApp().run()
