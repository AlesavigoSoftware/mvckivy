import configparser
import json
from dataclasses import dataclass, field
from typing import Self


EXCEPTION_POPUP_KV = """
#:import Window kivy.core.window.Window
#:import get_color_from_hex kivy.utils.get_color_from_hex


Popup:
    id: p
    title: "Exception caught!"
    size_hint: (0.9, 0.9)
    text: ""

    MDScrollView:
        id: scroll
        scroll_y: 0
        md_bg_color: get_color_from_hex("#e50000")

        MDBoxLayout:
            orientation: "vertical"

            Label:
                id: lbl
                text_size: (Window.width - 100, None)
                size_hint_y: None
                text: root.text
                texture_size: self.size

            MDButton:
                text: "Закрыть"
                style: "elevated"
                on_release: p.dismiss()
"""


@dataclass
class HotReloadConfig:
    kv_files: list[str] = field(default_factory=list)
    kv_dirs: list[str] = field(default_factory=list)
    autoreloader_paths: list[tuple[str, dict[str, bool | str]]] = field(
        default_factory=lambda: [(".", {"recursive": True})]
    )
    autoreloader_ignore_patterns: list[str] = field(
        default_factory=lambda: ["*.pyc", "*__pycache__*"]
    )
    classes: dict[str, str] = field(default_factory=dict)
    screen_names: list[str] = field(default_factory=list)

    def from_manual(
        self,
        kv_files: list[str] | None = None,
        kv_dirs: list[str] | None = None,
        autoreloader_paths: list[tuple[str, dict[str, bool | str]]] | None = None,
        autoreloader_ignore_patterns: list[str] | None = None,
        classes: dict[str, str] | None = None,
        screen_names: list[str] | None = None,
    ) -> Self:
        if kv_files is not None:
            self.kv_files = kv_files
        if kv_dirs is not None:
            self.kv_dirs = kv_dirs
        if autoreloader_paths is not None:
            self.autoreloader_paths = autoreloader_paths
        if autoreloader_ignore_patterns is not None:
            self.autoreloader_ignore_patterns = autoreloader_ignore_patterns
        if classes is not None:
            self.classes = classes
        if screen_names is not None:
            self.screen_names = screen_names
        return self

    def from_code(self, cfg: dict) -> Self:
        return self.from_manual(
            kv_files=cfg.get("kv_files"),
            kv_dirs=cfg.get("kv_dirs"),
            autoreloader_paths=cfg.get("autoreloader_paths"),
            autoreloader_ignore_patterns=cfg.get("autoreloader_ignore_patterns"),
            classes=cfg.get("classes"),
            screen_names=cfg.get("screen_names"),
        )

    def from_json(self, source: str, is_path: bool = True) -> Self:
        if is_path:
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(source)
        return self.from_code(data or {})

    def from_yaml(self, source: str, is_path: bool = True) -> Self:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML data") from e
        if is_path:
            with open(source, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(source)
        return self.from_code(data or {})

    def from_ini(self, path: str = "hotreload.ini", section: str = "hotreload") -> Self:
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return self

        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")
        if not cfg.has_section(section):
            return self

        def get_list(key: str) -> list[str]:
            return [item.strip() for item in cfg.get(section, key, fallback="").split(",") if item.strip()]

        kv_files = get_list("kv_files")
        kv_dirs = get_list("kv_dirs")
        autoreloader_paths = get_list("autoreloader_paths")
        autoreloader_ignore_patterns = get_list("autoreloader_ignore_patterns")


        classes: dict[str, str] = {}
        raw_classes = cfg.get(section, "classes", fallback="")
        for part in raw_classes.split(","):
            if "=" in part:
                name, mod = part.split("=", 1)
                name = name.strip()
                mod = mod.strip()
                if name and mod:
                    classes[name] = mod

        screen_names = get_list("screen_names")

        return self.from_manual(
            kv_files=kv_files or None,
            kv_dirs=kv_dirs or None,
            autoreloader_paths=autoreloader_paths or None,
            autoreloader_ignore_patterns=autoreloader_ignore_patterns or None,
            classes=classes or None,
            screen_names=screen_names or None,
        )

    def from_pyproject(self, path: str = "pyproject.toml", section: str = "tool.mvckivy") -> Self:
        try:
            import toml
        except Exception as e:
            raise ImportError("toml is required to load pyproject.toml") from e

        data = toml.load(path)
        node = data
        for part in section.split("."):
            node = node.get(part, {})
        return self.from_code(node or {})
