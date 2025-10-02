from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

from kivy.properties import ObjectProperty
from kivy.weakproxy import WeakProxy
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import TransitionBase

from kivymd.uix.screen import MDScreen
from kivymd.uix.transition import MDFadeSlideTransition

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.uix.behaviors import MKVAdaptiveBehavior, MVCBehavior
from mvckivy.uix.screen_manager import MKVScreenManager


if TYPE_CHECKING:
    from kivymd.uix.transition.transition import MDTransitionBase


logger = logging.getLogger("mvckivy")


class BaseScreen(AliasDedupeMixin, MVCBehavior, MKVAdaptiveBehavior, MDScreen):
    screen_manager: ObjectProperty[WeakProxy[MKVScreenManager] | None] = ObjectProperty(
        None, allownone=True
    )

    def _get_alias_md_bg_color(self, prop: ExtendedAliasProperty):
        return self._calc_alias_md_bg_color(prop)

    def _calc_alias_md_bg_color(self, prop: ExtendedAliasProperty):
        return self.theme_cls.backgroundColor

    alias_md_bg_color = ExtendedAliasProperty(
        _get_alias_md_bg_color,
        None,
        bind=["theme_cls.theme_style", "theme_cls.bg_darkening"],
        cache=True,
        rebind=True,
    )

    def __init__(self, *args, ignore_parent_mvc=True, **kwargs):
        super().__init__(*args, ignore_parent_mvc=ignore_parent_mvc, **kwargs)
        self._default_transition: TransitionBase | None = None

    def emit_default_transition(self) -> TransitionBase:
        if self._default_transition is None:
            self._default_transition = MDFadeSlideTransition(duration=0.3)

        return self._default_transition

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MKVScreenManager):
            if not self.screen_manager:
                self.screen_manager = WeakProxy(widget)
            return super().add_widget(widget, *args, **kwargs)

        elif isinstance(widget, BaseScreen):
            if self.screen_manager:
                return self.screen_manager.add_widget(widget, *args, **kwargs)
            else:
                logger.warning("On screen '%s' screen_manager is None", self.name)
                return super().add_widget(widget, *args, **kwargs)

        return super().add_widget(widget, *args, **kwargs)

    def on_parent(self, instance: Self, parent: Widget | None):
        if not parent:
            if self.screen_manager:
                self.screen_manager.clear_widgets()
                self.screen_manager = None
            self.clear_widgets()
        else:
            return super().on_parent(instance, parent)

    def on_enter(self, *args) -> None:
        return super().on_enter(*args)

    def on_leave(self, *args) -> None:
        return super().on_leave(*args)

    def switch_screen(
        self,
        screen_name: str,
        transition: TransitionBase | None = None,
    ) -> None:
        if transition is None:
            transition = self.emit_default_transition()

        if self.screen_manager:

            self.screen_manager.transition = transition

            if screen_name not in self.screen_manager.screen_names:
                logger.warning(
                    "Screen '%s' not found in screen manager '%s'. Available screens: %s",
                    screen_name,
                    self.screen_manager.name,
                    self.screen_manager.screen_names,
                )
            else:
                self.screen_manager.current = screen_name

        else:
            logger.warning("Screen manager is not set for screen '%s'", self.name)
