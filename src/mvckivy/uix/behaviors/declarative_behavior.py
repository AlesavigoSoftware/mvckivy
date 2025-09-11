from weakref import WeakValueDictionary

from kivy.properties import StringProperty
from kivy.uix.widget import Widget


class DeclarativeBehavior:
    """
    Implements the creation and addition of child widgets as declarative
    programming style.
    """

    id = StringProperty()
    __ids: WeakValueDictionary[str, Widget] = WeakValueDictionary()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for child in args:
            if isinstance(child, Widget):
                if getattr(child, "id", None):
                    self.__ids[child.id] = child
                else:
                    self.__ids[str(hash(child))] = child

    def on_kv_post(self, *args):
        """Makes DeclarativeBehavior behave as classic kv lang. Now it unifies imperative and declarative styles."""

        for child in self.__ids.values():
            if isinstance(child, Widget):
                self.add_widget(child)

    def add_widget(self, widget: Widget, *largs) -> None:
        pass

    def get_ids(self) -> WeakValueDictionary[str, Widget]:
        """
        Returns a dictionary of widget IDs defined in Python
        code that is written in a declarative style.
        """

        return self.__ids
