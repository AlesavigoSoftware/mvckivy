from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable, Self

from kivy.factory import Factory
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    Clock,
)
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivymd.uix.boxlayout import MDBoxLayout

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.uix.dialog import MKVDialog
from mvckivy.uix.list import MKVListItem


_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class MKVSettingsPanel(AliasDedupeMixin, MDBoxLayout):
    name = StringProperty("")
    title = StringProperty("")
    icon = StringProperty("tune")
    order = NumericProperty(0)
    settings_ref = ObjectProperty(None, rebind=True, allownone=True)
    orientation = "vertical"
    spacing = 0
    padding = (0, 0, 0, 0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._items: list[MKVSettingItemBase] = []

    def add_widget(self, widget, *args: Any, **kwargs: Any):
        if isinstance(widget, MKVSettingItemBase):
            self._items.append(widget)
            widget.panel_ref = self
            widget.settings_ref = self.settings_ref
            if self.settings_ref is not None:
                self.settings_ref.dispatch("on_item_registered", widget)
        return super().add_widget(widget, *args, **kwargs)

    def remove_widget(self, widget):
        if isinstance(widget, MKVSettingItemBase):
            if widget in self._items:
                self._items.remove(widget)
            if self.settings_ref is not None:
                self.settings_ref.dispatch("on_item_unregistered", widget)
            widget.panel_ref = None
            widget.settings_ref = None
        return super().remove_widget(widget)

    def iter_items(self) -> Iterable[MKVSettingItemBase]:
        return tuple(self._items)


class MKVSettingsNav(AliasDedupeMixin, MDBoxLayout):
    axis = OptionProperty("x", options=("x", "y"))
    items_container = ObjectProperty(None, rebind=True, allownone=True)
    orientation = "vertical"


class MKVSettingsNavItem(AliasDedupeMixin, ButtonBehavior, MDBoxLayout):
    panel_name = StringProperty("")
    panel_title = StringProperty("")
    panel_icon = StringProperty("tune")
    selected = BooleanProperty(False)
    settings_ref = ObjectProperty(None, rebind=True, allownone=True)
    orientation = "horizontal"

    def on_release(self):
        settings = self.settings_ref
        if settings is not None and self.panel_name:
            settings.switch_to(self.panel_name)


class MKVSettingsBase(AliasDedupeMixin, MDBoxLayout):
    orientation = "vertical"
    panels = ListProperty([])
    active_panel_name = StringProperty("")
    active_panel = ObjectProperty(None, rebind=True, allownone=True)
    nav_axis = OptionProperty("x", options=("x", "y"))

    nav_container = ObjectProperty(None, rebind=True, allownone=True)
    nav_items_box = ObjectProperty(None, rebind=True, allownone=True)
    content_container = ObjectProperty(None, rebind=True, allownone=True)

    __events__ = (
        "on_panel_added",
        "on_panel_removed",
        "on_active_panel",
        "on_item_registered",
        "on_item_unregistered",
        "on_item_value_changed",
        "on_dispatch_new_val",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._nav_items: dict[str, MKVSettingsNavItem] = {}
        self._pending_panels: list[MKVSettingsPanel] = []
        self._flush_trigger = Clock.create_trigger(self._flush_pending_panels, 0)

    def on_panel_added(self, panel: MKVSettingsPanel) -> None:
        pass

    def on_panel_removed(self, instance: Self, panel: MKVSettingsPanel) -> None:
        pass

    def on_active_panel(self, *args) -> None:
        pass

    def on_item_registered(self, item: MKVSettingItemBase) -> None:
        pass

    def on_item_unregistered(self, item: MKVSettingItemBase) -> None:
        pass

    def on_item_value_changed(
        self, item: MKVSettingItemBase, old_value: Any, new_value: Any
    ) -> None:
        pass

    def on_dispatch_new_val(self, key: str, value: Any) -> None:
        pass

    def add_widget(self, widget, *args: Any, **kwargs: Any):
        if isinstance(widget, MKVSettingsPanel):
            self._pending_panels.append(widget)
            self._flush_trigger()
            return widget
        return super().add_widget(widget, *args, **kwargs)

    def _flush_pending_panels(self, *_: Any) -> None:
        while self._pending_panels:
            panel = self._pending_panels.pop(0)
            self.add_panel(panel)

    def add_panel(self, panel: MKVSettingsPanel) -> None:
        if panel in self.panels:
            return
        if not panel.name:
            panel.name = f"panel_{len(self.panels) + 1}"
        panel.settings_ref = self
        self.panels.append(panel)
        self.panels.sort(key=lambda p: p.order)
        for item in panel.iter_items():
            item.settings_ref = self
            self.dispatch("on_item_registered", item)
        self.dispatch("on_panel_added", panel)
        self._ensure_nav_item(panel)
        if not self.active_panel:
            self.switch_to(panel.name)
        else:
            self._reorder_nav_items()

    def remove_panel(self, name: str) -> None:
        panel = self.get_panel(name)
        if panel is None:
            return
        if panel is self.active_panel and self.content_container:
            self.content_container.remove_widget(panel)
        for item in panel.iter_items():
            self.dispatch("on_item_unregistered", item)
            if item.settings_ref is self:
                item.settings_ref = None
        if panel in self.panels:
            self.panels.remove(panel)
        self.dispatch("on_panel_removed", panel)
        nav_item = self._nav_items.pop(panel.name, None)
        if nav_item is not None and self.nav_items_box is not None:
            self.nav_items_box.remove_widget(nav_item)
        panel.settings_ref = None
        if self.panels:
            self.switch_to(self.panels[0].name)
        else:
            self.active_panel = None
            self.active_panel_name = ""

    def get_panel(self, name: str) -> MKVSettingsPanel | None:
        for panel in self.panels:
            if panel.name == name:
                return panel
        return None

    def switch_to(self, name: str) -> None:
        panel = self.get_panel(name)
        if panel is None or panel is self.active_panel:
            return
        if self.content_container is not None:
            self.content_container.clear_widgets()
            self.content_container.add_widget(panel)
        previous = self.active_panel
        self.active_panel = panel
        self.active_panel_name = panel.name
        self.dispatch("on_active_panel", panel)
        if previous is not None:
            nav_prev = self._nav_items.get(previous.name)
            if nav_prev:
                nav_prev.selected = False
        nav_item = self._nav_items.get(panel.name)
        if nav_item:
            nav_item.selected = True

    def collect_items(
        self, panel: MKVSettingsPanel | None = None
    ) -> list["MKVSettingItemBase"]:
        target = panel or self.active_panel
        if target is None:
            return []
        return [
            item for item in target.iter_items() if isinstance(item, MKVSettingItemBase)
        ]

    def dispatch_new_val(self, key: str, value: Any) -> None:
        self.dispatch("on_dispatch_new_val", key, value)

    def _ensure_nav_item(self, panel: MKVSettingsPanel) -> None:
        nav_box = self.nav_items_box
        if nav_box is None:
            return
        nav_item = self._nav_items.get(panel.name)
        if nav_item is None:
            nav_item = Factory.MKVSettingsNavItem()
            nav_item.panel_name = panel.name
            nav_item.settings_ref = self
            self._nav_items[panel.name] = nav_item
        nav_item.panel_title = panel.title or panel.name
        nav_item.panel_icon = panel.icon
        if nav_item.parent is not nav_box:
            nav_box.add_widget(nav_item)
        self._reorder_nav_items()

    def _reorder_nav_items(self) -> None:
        nav_box = self.nav_items_box
        if nav_box is None:
            return
        nav_box.clear_widgets()
        for panel in self.panels:
            nav_item = self._nav_items.get(panel.name)
            if nav_item is None:
                continue
            nav_item.panel_title = panel.title or panel.name
            nav_item.panel_icon = panel.icon
            nav_box.add_widget(nav_item)


class MKVSettingsTop(MKVSettingsBase):
    nav_axis = "x"


class MKVSettingsRight(MKVSettingsBase):
    nav_axis = "y"


class MKVSettingItemBase(MKVListItem):
    key = StringProperty("")
    title = StringProperty("")
    subtitle = StringProperty("", allownone=True)
    icon = StringProperty("tune", allownone=True)
    value = ObjectProperty(None, rebind=True, allownone=True)
    default = ObjectProperty(None, allownone=True)
    enabled = BooleanProperty(True)
    visible = BooleanProperty(True)
    formatter = ObjectProperty(None, allownone=True)
    commit_mode = OptionProperty("on_save", options=("on_save", "on_validate"))
    validator = ObjectProperty(None, allownone=True)

    settings_ref = ObjectProperty(None, rebind=True, allownone=True)
    panel_ref = ObjectProperty(None, rebind=True, allownone=True)
    dialog_ref = ObjectProperty(None, rebind=True, allownone=True)
    display_value = StringProperty("")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._display_trigger = Clock.create_trigger(self._refresh_display, 0)
        self._refresh_display()

    def on_kv_post(self, base_widget) -> None:
        super().on_kv_post(base_widget)
        self._refresh_display()

    def on_value(self, *_: Any) -> None:
        self._display_trigger()

    def on_formatter(self, *_: Any) -> None:
        self._refresh_display()

    def on_visible(self, *_: Any) -> None:
        self.opacity = 1.0 if self.visible else 0.0
        self.disabled = not self.visible or not self.enabled

    def on_enabled(self, *_: Any) -> None:
        self.disabled = not self.enabled or not self.visible

    def _refresh_display(self, *_: Any) -> None:
        value = self.value
        formatter = self.formatter
        if callable(formatter):
            try:
                value = formatter(value)
            except Exception:  # pragma: no cover - defensive
                value = self.value
        self.display_value = str(value)

    def open_dialog(self) -> None:
        dialog = self.dialog_ref
        if dialog:
            dialog.open()
            return
        dialog = self._create_dialog()
        dialog.bind(on_dismiss=lambda *_: self._release_dialog())
        dialog.open()
        self.dialog_ref = dialog

    def _create_dialog(self) -> "MKVSettingsDialogBase":  # pragma: no cover
        raise NotImplementedError

    def _release_dialog(self) -> None:
        self.dialog_ref = None

    def commit_value(self, new_value: Any) -> None:
        old_value = self.value
        if old_value == new_value:
            return
        self.value = new_value
        settings = self.settings_ref
        if settings is not None:
            settings.dispatch("on_item_value_changed", self, old_value, new_value)
            if self.key:
                settings.dispatch_new_val(self.key, new_value)


class MKVSettingBooleanItem(MKVSettingItemBase):
    value = BooleanProperty(False)

    def toggle(self, *_: Any) -> None:
        if self.enabled:
            self.commit_value(not bool(self.value))


class MKVSettingStringItem(MKVSettingItemBase):
    def _create_dialog(self) -> "MKVSettingsDialogBase":
        return MKVSettingsStringDialog()


class MKVSettingPathItem(MKVSettingItemBase):
    path_mode = OptionProperty("file", options=("file", "dir"))
    must_exist = BooleanProperty(True)
    filters = ListProperty([])

    def _create_dialog(self) -> "MKVSettingsDialogBase":
        return MKVSettingsPathDialog(
            path_mode=self.path_mode,
            must_exist=self.must_exist,
            filters=list(self.filters),
        )


class MKVSettingColorItem(MKVSettingItemBase):
    def _create_dialog(self) -> "MKVSettingsDialogBase":
        return MKVSettingsColorDialog(current_value=self.value or "#FFFFFFFF")


class MKVSettingsDialogBase(MKVDialog):
    commit_mode = OptionProperty("on_save", options=("on_save", "on_validate"))
    validator = ObjectProperty(None, allownone=True)
    current_value = ObjectProperty(None, rebind=True, allownone=True)
    item_ref = ObjectProperty(None, rebind=True, allownone=True)
    validation_error = StringProperty("")
    dialog_title = StringProperty("")
    confirm_text = StringProperty("Save")
    cancel_text = StringProperty("Cancel")

    def on_open(self, *_: Any) -> None:
        super().on_open(*_)
        self.update_current_value(self.current_value, trigger_commit=False)

    def update_current_value(self, value: Any, *, trigger_commit: bool = False) -> None:
        norm_value = value if value is not None else ""
        self.current_value = norm_value
        ok = self._update_validation_state(norm_value)
        if trigger_commit and self.commit_mode == "on_validate" and ok:
            self._commit_value(norm_value)

    def confirm(self, *_: Any) -> None:
        value = self.current_value if self.current_value is not None else ""
        if self._update_validation_state(value):
            self._commit_value(value)

    def validate(self, value: Any) -> tuple[bool, str | None]:
        validator = self.validator
        if not callable(validator):
            return True, None
        try:
            result = validator(value)
        except Exception as exc:  # pragma: no cover - defensive
            return False, str(exc)
        if isinstance(result, tuple):
            ok = bool(result[0])
            message = result[1] if len(result) > 1 else None
            return ok, message
        return bool(result), None

    def _update_validation_state(self, value: Any) -> bool:
        ok, message = self.validate(value)
        self.validation_error = message or "" if not ok else ""
        self.on_validation_error()
        return ok

    def _commit_value(self, value: Any) -> None:
        item = self.item_ref
        if item is not None:
            item.commit_value(value)
        self.dismiss()

    def on_validation_error(self) -> None:  # pragma: no cover - UI hook
        pass


class MKVSettingsTextDialog(MKVSettingsDialogBase):
    input_field = ObjectProperty(None, rebind=True, allownone=True)

    def on_open(self, *_: Any) -> None:
        super().on_open(*_)
        field = self.input_field
        if field is not None:
            field.text = self.current_value or ""
            field.focus = True
        self.on_validation_error()

    def on_validation_error(self) -> None:
        field = self.input_field
        if field is not None:
            field.helper_text = self.validation_error


class MKVSettingsStringDialog(MKVSettingsTextDialog):
    pass


class MKVSettingsPathDialog(MKVSettingsTextDialog):
    path_mode = OptionProperty("file", options=("file", "dir"))
    must_exist = BooleanProperty(True)
    filters = ListProperty([])

    confirm_text = StringProperty("Choose")

    def on_open(self, *_: Any) -> None:
        super().on_open(*_)
        field = self.input_field
        if field is not None:
            field.text = self.current_value or ""
            field.focus = True
        self.on_validation_error()

    def validate(self, value: Any) -> tuple[bool, str | None]:
        text = str(value or "")
        if not text:
            return super().validate(text)
        path = Path(text)
        if self.must_exist and not path.exists():
            return False, "Path does not exist"
        if self.path_mode == "dir" and not path.is_dir():
            return False, "Directory required"
        if self.path_mode == "file" and self.filters:
            suffix = path.suffix.lower()
            filters = {f.lower() for f in self.filters}
            if suffix and suffix not in filters:
                return False, "Invalid extension"
        return super().validate(text)

    def on_validation_error(self) -> None:
        field = self.input_field
        if field is not None:
            field.helper_text = self.validation_error


class MKVSettingsColorDialog(MKVSettingsDialogBase):
    hex_field = ObjectProperty(None, rebind=True, allownone=True)
    preview_box = ObjectProperty(None, rebind=True, allownone=True)

    confirm_text = StringProperty("Apply")

    def on_open(self, *_: Any) -> None:
        super().on_open(*_)
        field = self.hex_field
        if field is not None:
            field.text = self.current_value or "#FFFFFFFF"
        self._sync_preview()

    def validate(self, value: Any) -> tuple[bool, str | None]:
        text = str(value or "").strip()
        if not text:
            return False, "Value required"
        if not _HEX_COLOR_RE.match(text):
            return False, "Use #RRGGBB or #RRGGBBAA"
        return super().validate(text)

    def update_current_value(self, value: Any, *, trigger_commit: bool = False) -> None:
        super().update_current_value(value, trigger_commit=trigger_commit)
        self._sync_preview()

    def _sync_preview(self) -> None:
        box = self.preview_box
        if box is None:
            return
        value = self.current_value or "#FFFFFFFF"
        try:
            color = get_color_from_hex(value)
        except Exception:  # pragma: no cover - defensive
            color = (1.0, 1.0, 1.0, 1.0)
        box.md_bg_color = color
