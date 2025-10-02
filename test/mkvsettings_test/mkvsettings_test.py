from __future__ import annotations

from pathlib import Path
from typing import Any

from kivy.lang import Builder

from mvckivy.app import MKVApp
from mvckivy.uix.settings.settings import MKVSettingsBase


REPO_ROOT = Path(__file__).resolve().parents[2]
LIST_KV_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "list" / "list.kv"
DIALOG_KV_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "dialog" / "dialog.kv"
SETTINGS_KV_PATH = REPO_ROOT / "src" / "mvckivy" / "uix" / "settings" / "settings.kv"


class SettingsDemoApp(MKVApp):
    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Light"
        for path in (LIST_KV_PATH, DIALOG_KV_PATH, SETTINGS_KV_PATH):
            Builder.load_file(str(path))
        root = Builder.load_file("mkvsettings_test.kv")
        for widget_id in ("top_settings", "right_settings"):
            widget = root.ids.get(widget_id)
            if isinstance(widget, MKVSettingsBase):
                widget.bind(
                    on_dispatch_new_val=self._on_dispatch,
                    on_item_value_changed=self._on_item_value,
                )
        return root

    def _on_dispatch(self, settings: MKVSettingsBase, key: str, value: Any) -> None:
        print(f"dispatch_new_val -> {settings.__class__.__name__}: {key}={value!r}")

    def _on_item_value(
        self,
        settings: MKVSettingsBase,
        item,
        old_value: Any,
        new_value: Any,
    ) -> None:
        print(
            "item_value_changed ->",
            settings.__class__.__name__,
            getattr(item, "key", ""),
            old_value,
            "->",
            new_value,
        )


if __name__ == "__main__":
    SettingsDemoApp().run()
