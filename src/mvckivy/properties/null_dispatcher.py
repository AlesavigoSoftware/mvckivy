from kivy.event import EventDispatcher
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
    ListProperty,
    DictProperty,
)


class ConstNullDispatcher(EventDispatcher):
    """Универсальный контроллер: значения из __getattr__/__setattr__, без Kivy-Property."""

    def __init__(self, **defaults):
        super().__init__()
        object.__setattr__(self, "_vals", dict(defaults))

    def __getattr__(self, name):
        vals = object.__getattribute__(self, "_vals")
        if name in vals:
            return vals[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith("_") or name in type(self).__dict__:
            return object.__setattr__(self, name, value)
        vals = object.__getattribute__(self, "_vals")
        vals[name] = value
        # ВАЖНО: здесь НЕТ dispatch — KV об этом не узнает.


def _prop_for(value):
    if isinstance(value, bool):
        return BooleanProperty(value)
    if isinstance(value, (int, float)):
        return NumericProperty(value)
    if isinstance(value, str):
        return StringProperty(value)
    if isinstance(value, (list, tuple)):
        return ListProperty(list(value))
    if isinstance(value, dict):
        return DictProperty(value)
    return ObjectProperty(value, allownone=True)


def create_null_dispatcher(**defaults):
    # Динамически создаём подкласс EventDispatcher с Kivy-свойствами на классе
    attrs = {name: _prop_for(val) for name, val in defaults.items()}
    cls = type(f"NullDispatcher_{id(defaults)}", (EventDispatcher,), attrs)
    return cls()
