from contextlib import suppress

from typing import TypeVar, Optional

from kivy.uix.widget import Widget


class SaveLastParentMixin(Widget):
    T = TypeVar("T", bound=Widget)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_parent: Optional[SaveLastParentMixin.T] = None

    def on_parent(self, widget: T, parent: T):
        with suppress(AttributeError):
            super().on_parent(widget, parent)

        if parent is not None:
            self._last_parent = parent
