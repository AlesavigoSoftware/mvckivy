from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from kivy.properties import BooleanProperty, ObjectProperty
from kivy.weakproxy import WeakProxy

from kivymd.uix.screen import MDScreen
from kivymd.uix.transition import MDFadeSlideTransition

from mvckivy.uix.behaviors.base_screen_behavior import BaseScreenBehavior
from mvckivy.uix.behaviors import MTDBehavior
from mvckivy.uix.screen_manager import ConfiguredScreenManager


if TYPE_CHECKING:
    from kivymd.uix.transition.transition import MDTransitionBase


logger = logging.getLogger("mvckivy")


class BaseScreen(MDScreen, BaseScreenBehavior, MTDBehavior):
    screen_manager: ObjectProperty[WeakProxy[ConfiguredScreenManager] | None] = (
        ObjectProperty(None, allownone=True)
    )

    def __init__(self, *args, ignore_parent_mvc=True, **kwargs):
        super().__init__(*args, ignore_parent_mvc=ignore_parent_mvc, **kwargs)
        self.__default_transition: MDFadeSlideTransition = MDFadeSlideTransition(
            duration=0.3
        )

    def switch_tab(self, tab_name: str) -> None:
        """
        Switch to a specific tab in the screen manager.
        This method is a placeholder and should be implemented in subclasses.
        """
        logger.warning(
            "Method 'switch_tab' is not implemented for screen '%s'.", self.name
        )

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, ConfiguredScreenManager):
            self.screen_manager = WeakProxy(widget)
            return super().add_widget(widget, *args, **kwargs)

        elif isinstance(widget, BaseScreen):
            if self.screen_manager:
                return self.screen_manager.add_widget(widget, *args, **kwargs)
            else:
                logger.warning("On screen '%s' screen_manager is None", self.name)
                return super().add_widget(widget, *args, **kwargs)

        return super().add_widget(widget, *args, **kwargs)

    def on_parent(self, widget, parent):
        if not parent:
            if self.screen_manager:
                self.screen_manager.clear_widgets()
                self.screen_manager = None
            self.clear_widgets()
        else:
            return super().on_parent(widget, parent)

    def on_enter(self, *args):
        return super().on_enter(*args)

    def on_leave(self, *args):
        return super().on_leave(*args)

    def switch_screen(
        self,
        screen_name: str,
        transition: MDTransitionBase | None = None,
    ) -> None:
        if transition is None:
            transition = self.__default_transition

        if self.screen_manager:

            if self.screen_manager.transition is not transition:
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
