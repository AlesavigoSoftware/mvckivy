from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.navigationrail import (
    MDNavigationRailItem,
    MDNavigationRailItemIcon,
    MDNavigationRailItemLabel,
    MDNavigationRailFabButton,
    MDNavigationRailMenuButton,
    MDNavigationRail,
)
from kivymd_extensions.akivymd.uix.behaviors.labelanimation import (
    AKAnimationIconBehavior,
)

from mvckivy.uix.behaviors.hover_behavior import ButtonHoverBehavior
from mvckivy.uix.behaviors.mvc_behavior import MVCBehavior, ParentClassUnsupported
from mvckivy.uix.layout.mvc_box_layout import MVCBoxLayout


class NavigationRailItem(MDNavigationRailItem, MVCBehavior):
    text = StringProperty()
    icon = StringProperty()
    theme_font_name = StringProperty()
    font_name = StringProperty()

    def _set_mvc_attrs_from_parent(self) -> None:
        try:
            super()._set_mvc_attrs_from_parent()
        except ParentClassUnsupported:
            self._ignore_parent_mvc = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_widget = NavigationRailItemIcon(icon=self.icon)
        label_kwargs = {
            "text": self.text,
            "theme_font_name": self.theme_font_name or "Custom",
        }
        if self.font_name:
            label_kwargs["font_name"] = self.font_name

        label_widget = NavigationRailItemLabel(**label_kwargs)

        super(NavigationRailItem, self).add_widget(icon_widget)
        super(NavigationRailItem, self).add_widget(label_widget)

        self.ids["item_icon"] = icon_widget
        self.ids["item_label"] = label_widget

        self.bind(icon=icon_widget.setter("icon"))
        self.bind(text=label_widget.setter("text"))
        self.bind(theme_font_name=label_widget.setter("theme_font_name"))
        self.bind(font_name=label_widget.setter("font_name"))


class NavigationRailItemIcon(MDNavigationRailItemIcon):
    def finish_ripple(self) -> None:
        if self._doing_ripple and not self._finishing_ripple:
            self._finishing_ripple = True
            self._doing_ripple = False
            Animation.cancel_all(self, "_ripple_rad")
            self.fade_out()

    def fade_out(self, *args) -> None:
        rc = self.ripple_color
        if not self._fading_out:
            self._fading_out = True
            Animation.cancel_all(self, "ripple_color")
            self.anim_complete()

    def anim_complete(self, *args) -> None:
        """Fired when the "fade_out" animation complete."""

        self._doing_ripple = False
        self._finishing_ripple = False
        self._fading_out = False

        if not self.ripple_canvas_after:
            canvas = self.canvas.before
        else:
            canvas = self.canvas.after

        canvas.remove_group("circular_ripple_behavior")
        canvas.remove_group("rectangular_ripple_behavior")

        self.on_release()

    def on_release(self):
        self.parent.dispatch("on_release")


class NavigationRailItemLabel(MDNavigationRailItemLabel):
    pass


class NavigationRailButton(
    MDNavigationRailFabButton, ButtonHoverBehavior, AKAnimationIconBehavior
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.elevation = 1
        self._last_parent = None

    def on_parent(self, widget, parent):
        if parent is None and self._last_parent is not None:
            self._last_parent.add_widget(self)
            self.opacity = 1
            anim = Animation(opacity=0, duration=0.5)
            anim.bind(on_complete=self._remove_widget)
            anim.start(self)
        elif parent is not None:
            self._last_parent = parent
            self.opacity = 0
            anim = Animation(opacity=1, duration=0.5)
            anim.start(self)

    def _remove_widget(self, *args):
        lp = self._last_parent
        self._last_parent = None
        lp.remove_widget(self)


class NavigationRailMenuButton(MDNavigationRailMenuButton, ButtonHoverBehavior):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("icon", "menu")
        super().__init__(*args, **kwargs)

    def on_release(self):
        parent = self.parent
        toggle_panel = getattr(parent, "toggle_panel", None)
        if callable(toggle_panel):
            toggle_panel()
        super().on_release()


class NavigationRail(MDNavigationRail, MVCBehavior):
    panel_widget = ObjectProperty(None, rebind=True, allownone=True)

    def _set_mvc_attrs_from_parent(self) -> None:
        try:
            super()._set_mvc_attrs_from_parent()
        except ParentClassUnsupported:
            self._ignore_parent_mvc = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("size_hint", (None, 1))
        kwargs.setdefault("width", dp(80))
        kwargs.setdefault("anchor", "top")
        super().__init__(*args, **kwargs)

        self._upgrade_box_items_container()

        Clock.schedule_once(lambda *_: self._ensure_panel_reference())

        self.bind(type=lambda *_: self._update_spacing())
        self._update_spacing()
        try:
            self.theme_cls.bind(surfaceColor=lambda *_: self._update_background())
        except Exception:
            pass
        self._update_background()

    def _ensure_panel_reference(self) -> None:
        if self.panel_widget is not None:
            return

        for widget in self.walk_reverse():
            if widget is self:
                continue
            if isinstance(widget, MDNavigationDrawer):
                self.panel_widget = widget
                break

    def toggle_panel(self, state: str = "toggle") -> None:
        panel = self.panel_widget
        if panel is None:
            self._ensure_panel_reference()
            panel = self.panel_widget

        if panel is None:
            return

        set_state = getattr(panel, "set_state", None)
        if callable(set_state):
            set_state(state)

    def open_panel(self) -> None:
        self.toggle_panel(state="open")

    def close_panel(self) -> None:
        self.toggle_panel(state="close")

    def _upgrade_box_items_container(self) -> None:
        box_items = self.ids.get("box_items")
        if box_items is None:
            return
        if isinstance(box_items, MVCBoxLayout):
            box_items.bind(
                minimum_size=lambda inst, value: setattr(inst, "size", value)
            )
            return

        new_box = MVCBoxLayout(
            orientation=box_items.orientation,
            size_hint=box_items.size_hint,
            pos_hint=getattr(box_items, "pos_hint", {"center_x": 0.5}),
        )
        new_box.spacing = box_items.spacing
        new_box.size = box_items.size
        new_box.bind(
            minimum_size=lambda inst, value: setattr(inst, "size", value)
        )

        parent = box_items.parent
        if parent is not None:
            index = parent.children.index(box_items)
            parent.remove_widget(box_items)
            parent.add_widget(new_box, index=index)

        for child in list(box_items.children):
            box_items.remove_widget(child)
            new_box.add_widget(child)

        self.ids["box_items"] = new_box

    def _update_spacing(self) -> None:
        spacing_map = {
            "selected": dp(12),
            "labeled": dp(52),
            "unselected": dp(20),
        }
        box_items = self.ids.get("box_items")
        if box_items:
            box_items.spacing = spacing_map.get(self.type, dp(20))

    def _update_background(self) -> None:
        if self.theme_bg_color == "Custom" and self.md_bg_color:
            return
        target = getattr(self.theme_cls, "surfaceColor", self.md_bg_color)
        if self.md_bg_color != target:
            self.md_bg_color = target
