from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder

from mvckivy.app import MKVApp
from mvckivy.uix.button.speed_dial import MKVSpeedDialAction


class FavoriteAction(MKVSpeedDialAction):
    """Example custom action with predefined icon."""

    def __init__(self, **kwargs):
        kwargs.setdefault("icon", "star")
        super().__init__(**kwargs)


REPO_ROOT = Path(__file__).resolve().parents[2]
KV_SPEED_DIAL_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "button" / "speed_dial.kv"


class DemoApp(MKVApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        Builder.load_file(str(KV_SPEED_DIAL_PATH))
        return Builder.load_file("mkvspeeddial.kv")

    def on_add_point(self):
        print("Add point")

    def on_download(self):
        print("Download")

    def on_stats(self):
        print("Statistics")

    def on_edit(self):
        print("Edit")


if __name__ == "__main__":
    DemoApp().run()
