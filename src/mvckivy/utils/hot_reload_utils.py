import configparser
import json
from dataclasses import dataclass, field
from typing import Self
from pathlib import Path


EXCEPTION_POPUP_KV = """
Popup:
    id: p
    title: "Exception caught!"
    size_hint: (0.9, 0.9)
    text: ""
    ScrollView:
        id: scroll
        do_scroll_x: False
        scroll_y: 0
        
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
        
            Label:
                id: lbl
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                padding: 10, 10
                text: root.text
            
            MDButton:
                on_release: root.dismiss()
                style: "text"
                
                MDButtonText:
                    text: "Close"
                
                MDButtonIcon:
                    icon: "close"
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
    screens: list[dict] = field(default_factory=list)

    def _validate_paths(
        self,
        kv_files: list[str] | None = None,
        kv_dirs: list[str] | None = None,
        autoreloader_paths: list[tuple[str, dict[str, bool | str]]]
        | list[str]
        | None = None,
    ) -> None:
        invalid_files: list[str] = []
        invalid_dirs: list[str] = []
        invalid_autoreload: list[str] = []

        if kv_files is not None:
            for p in kv_files:
                if not Path(p).is_file():
                    invalid_files.append(p)

        if kv_dirs is not None:
            for p in kv_dirs:
                if not Path(p).is_dir():
                    invalid_dirs.append(p)

        if autoreloader_paths is not None:
            for entry in autoreloader_paths:
                path_str: str | None = None
                if isinstance(entry, (tuple, list)) and entry:
                    path_str = str(entry[0])
                elif isinstance(entry, str):
                    path_str = entry
                else:
                    path_str = None

                if not path_str or not Path(path_str).exists():
                    invalid_autoreload.append(str(entry))

        msgs: list[str] = []
        if invalid_files:
            msgs.append(
                "kv_files not found or not files: " + ", ".join(invalid_files)
            )
        if invalid_dirs:
            msgs.append(
                "kv_dirs not found or not directories: " + ", ".join(invalid_dirs)
            )
        if invalid_autoreload:
            msgs.append(
                "autoreloader_paths contain missing paths: "
                + ", ".join(invalid_autoreload)
            )
        if msgs:
            raise ValueError("; ".join(msgs))

    def _validate_screens(self, screens: list[dict] | None) -> None:
        if screens is None:
            return
        for entry in screens:
            try:
                if entry.get("name") == "app_screen":
                    raise ValueError(
                        "'app_screen' is a reserved name and cannot appear in 'screens'"
                    )
            except AttributeError:
                # Ignore non-dict entries here; other consumers may validate shape
                pass

    def from_manual(
        self,
        kv_files: list[str] | None = None,
        kv_dirs: list[str] | None = None,
        autoreloader_paths: list[tuple[str, dict[str, bool | str]]] | None = None,
        autoreloader_ignore_patterns: list[str] | None = None,
        classes: dict[str, str] | None = None,
        screens: list[dict] | None = None,
    ) -> Self:
        # Validate provided inputs before assignment
        self._validate_paths(kv_files, kv_dirs, autoreloader_paths)
        self._validate_screens(screens)
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
        if screens is not None:
            self.screens = screens
        return self

    def from_code(self, cfg: dict) -> Self:
        return self.from_manual(
            kv_files=cfg.get("kv_files"),
            kv_dirs=cfg.get("kv_dirs"),
            autoreloader_paths=cfg.get("autoreloader_paths"),
            autoreloader_ignore_patterns=cfg.get("autoreloader_ignore_patterns"),
            classes=cfg.get("classes"),
            screens=cfg.get("screens"),
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

        # Parse screens as JSON list of dicts: [{"name": "...", "recreate_children": true}, ...]
        raw_screens = cfg.get(section, "screens", fallback="").strip()
        screens: list[dict] = []
        if raw_screens:
            try:
                screens = json.loads(raw_screens)
                if not isinstance(screens, list):
                    raise ValueError("'screens' must be a JSON list")
            except Exception as e:
                raise ValueError("Invalid 'screens' format in INI; expected JSON list of dicts") from e

        return self.from_manual(
            kv_files=kv_files or None,
            kv_dirs=kv_dirs or None,
            autoreloader_paths=autoreloader_paths or None,
            autoreloader_ignore_patterns=autoreloader_ignore_patterns or None,
            classes=classes or None,
            screens=screens or None,
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
