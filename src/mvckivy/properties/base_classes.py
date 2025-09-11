from __future__ import annotations

import weakref
from copy import deepcopy

from kivy.properties import AliasProperty
from typing import Callable, Any, Type

from kivy.event import EventDispatcher


def dispatch_on_result(func: Callable):
    def wrapper(self: ObservableStruct, *args):
        res = func(self, *args)
        self.last_op = (func.__name__, args)

        if not self._enable_on_change_only:
            self.dispatcher.dispatch(f"on_{self.last_op[0]}", self, self.last_op[1])

        self.dispatcher.dispatch("on_change", self._parent_prop, self, self.last_op)

        if self._dispatch_on_change_to_prop:
            for name, observer in self._parent_prop.bound_observers.items():
                self._parent_prop.dispatch(observer)

        return res

    return wrapper


class ObservableStructDispatcher(EventDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_change")

    def on_change(
        self,
        prop: ExtendedStructProperty,
        data: ObservableStruct,
        last_op: tuple[str | None, tuple[Any] | None],
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
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.last_op: tuple[str | None, tuple[Any] | None] = (None, None)
        self.dispatcher = dispatcher
        self._parent_prop = parent_prop
        self._dispatch_on_change_to_prop = dispatch_on_change_to_prop
        self._enable_on_change_only = enable_on_change_only


class ObserversCollectorMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_observers: weakref.WeakValueDictionary[str, EventDispatcher] = (
            weakref.WeakValueDictionary()
        )

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
        **kwargs,
    ):
        super().__init__(getter=self._getter, setter=self._setter, **kwargs)
        self._struct_cls = struct_cls
        self._dispatcher = dispatcher
        self._default = defaultvalue
        self._dispatch_on_change_to_prop = dispatch_on_change_to_prop
        self._enable_on_change_only = enable_on_change_only
        self._values = weakref.WeakKeyDictionary()

    def _get_or_create(self, inst):

        if inst is None:
            return self

        if inst not in self._values:
            self._values[inst] = self._struct_cls(
                self,
                self._dispatch_on_change_to_prop,
                self._enable_on_change_only,
                self._dispatcher,
                deepcopy(self._default),
            )

        return self._values[inst]

    def _getter(self, inst):
        return self._get_or_create(inst)

    def _setter(self, inst, value):
        cur = self._get_or_create(inst)

        if value is cur:
            return False

        self._values[inst] = self._struct_cls(
            self,
            self._dispatch_on_change_to_prop,
            self._enable_on_change_only,
            self._dispatcher,
            value,
        )

        return True
