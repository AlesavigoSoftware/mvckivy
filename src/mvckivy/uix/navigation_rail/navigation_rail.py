from kivy.animation import Animation
from kivy.properties import StringProperty
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

from mvckivy import ButtonHoverBehavior, MVCBehavior


class NavigationRailItem(MDNavigationRailItem, MVCBehavior):
    text = StringProperty()
    icon = StringProperty()
    theme_font_name = StringProperty()
    font_name = StringProperty()


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
    pass


class NavigationRail(MDNavigationRail, MVCBehavior):
    pass
