"""Demo app for manual verification of MKVDialog layouts."""

from __future__ import annotations

from pathlib import Path

from kivy.factory import Factory
from kivy.lang import Builder
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

FACTORY_CLASSES = (
    MKVDialog,
    MKVDialogIcon,
    MKVDialogHeadlineText,
    MKVDialogSupportingText,
    MKVDialogContentContainer,
    MKVDialogButtonContainer,
    MDLabel,
    MDButton,
    MDButtonText,
    MDTextField,
)

# keep references so Kivy registers classes before KV loading
for _cls in FACTORY_CLASSES:
    Factory.register(_cls.__name__, cls=_cls)


class Root(MDBoxLayout):
    pass


class DialogTestApp(MKVApp):
    title = "MKVDialog Variations"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_dialog = None
        self._dialog_stack: list[MKVDialog] = []

    def build(self):
        if KV_DIALOG_PATH.exists():
            Builder.load_file(str(KV_DIALOG_PATH))
        return Builder.load_file(str(KV_TEST_PATH))

    def open_dialog(self, factory_name: str) -> None:
        dialog_cls = getattr(Factory, factory_name)
        dialog = dialog_cls()
        dialog.bind(on_dismiss=lambda *_: self._clear_active(dialog))
        if self._active_dialog is not None:
            self._dialog_stack.append(self._active_dialog)
        self._active_dialog = dialog
        dialog.open()

    def close_active_dialog(self) -> None:
        if self._active_dialog is not None:
            self._active_dialog.dismiss()

    def _clear_active(self, dialog) -> None:
        if dialog in self._dialog_stack:
            self._dialog_stack.remove(dialog)
        if self._active_dialog is dialog:
            self._active_dialog = self._dialog_stack.pop() if self._dialog_stack else None


if __name__ == "__main__":
    DialogTestApp().run()
