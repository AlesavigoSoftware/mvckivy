from __future__ import annotations

import weakref

from kivy.properties import AliasProperty, Property
from typing import Callable, Optional, Any, Type

from kivy.event import EventDispatcher


def dispatch_on_result(func: Callable):
    def wrapper(self: ObservableStruct, *args):
        res = func(self, *args)
        self.last_op = (func.__name__, args)

        if not self._enable_on_change_only:
            self.dispatcher.dispatch(f'on_{self.last_op[0]}', self, self.last_op[1])

        self.dispatcher.dispatch('on_change', self._parent_prop, self, self.last_op)

        if self._dispatch_on_change_to_prop:
            for name, observer in self._parent_prop.bound_observers.items():
                self._parent_prop.dispatch(observer)

        return res

    return wrapper


class ObservableStructDispatcher(EventDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type('on_change')

    def on_change(
            self,
            prop: ExtendedStructProperty,
            data: ObservableStruct,
            last_op: tuple[Optional[str], Optional[tuple[Any]]]
    ):
        pass


class ObservableStruct:
    def __init__(
            self,
            parent_prop: ExtendedStructProperty,
            dispatch_on_change_to_prop: bool,
            enable_on_change_only: bool,
            dispatcher: ObservableStructDispatcher,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.last_op: tuple[Optional[str], Optional[tuple[Any]]] = (None, None)
        self.dispatcher = dispatcher
        self._parent_prop = parent_prop
        self._dispatch_on_change_to_prop = dispatch_on_change_to_prop
        self._enable_on_change_only = enable_on_change_only


class ObserversCollectorMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_observers: weakref.WeakValueDictionary[str, EventDispatcher] = weakref.WeakValueDictionary()

    def link(self, EventDispatcher_obj, unicode_name):
        super().link(EventDispatcher_obj, unicode_name)
        self.bound_observers[unicode_name] = EventDispatcher_obj


class ExtendedStructProperty(ObserversCollectorMixin, AliasProperty):
    def __init__(
            self,
            struct_cls: Type[ObservableStruct],
            dispatcher: ObservableStructDispatcher,
            defaultvalue: Any,
            dispatch_on_change_to_prop: bool,
            enable_on_change_only: bool,
            **kwargs
    ):
        super().__init__(getter=self._getter, setter=self._setter, **kwargs)
        self._enable_on_change_only = enable_on_change_only
        self._dispatch_on_change_to_prop = dispatch_on_change_to_prop
        self._struct_cls = struct_cls

        self.data = self._struct_cls(
            self, self._dispatch_on_change_to_prop, self._enable_on_change_only, dispatcher, defaultvalue
        )

    def _getter(self, *_):
        return self.data

    def _setter(self, dispatcher, value: Any):
        if value is not self.data:

            self.data = self._struct_cls(
                self, self._dispatch_on_change_to_prop, self._enable_on_change_only, dispatcher, value
            )

            return True
