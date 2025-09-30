"""Demo app for manual verification of MKVLabel and MKVIcon."""

from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from mvckivy.app import MKVApp
from mvckivy.uix.label import MKVLabel, MKVIcon

from kivy.factory import Factory

_FACTORY_CLASSES = (MKVLabel, MKVIcon, MDLabel, MDButton, MDButtonText, MDScrollView)

for _cls in _FACTORY_CLASSES:
    Factory.register(_cls.__name__, cls=_cls)

REPO_ROOT = Path(__file__).resolve().parents[2]
KV_LABEL_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "label" / "label.kv"
KV_TEST_PATH = Path(__file__).with_name("mkvlabel_test.kv")


class Root(MDBoxLayout):
    pass


class LabelTestApp(MKVApp):
    title = "MKVLabel / MKVIcon"

    def build(self):
        if KV_LABEL_PATH.exists():
            Builder.load_file(str(KV_LABEL_PATH))
        Builder.load_file(str(KV_TEST_PATH))
        return Root()


if __name__ == "__main__":
    LabelTestApp().run()
