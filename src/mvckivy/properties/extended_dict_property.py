from __future__ import annotations

from mvckivy.properties.base_classes import (
    ObservableStructDispatcher,
    ObservableStruct,
    dispatch_on_result,
    ExtendedStructProperty,
)


class ObservableDictDispatcher(ObservableStructDispatcher):
    __events__ = (
        "on_clear",
        "on_pop",
        "on_popitem",
        "on_setdefault",
        "on_update",
        "on___delitem__",
        "on___setitem__",
    )

    def on_clear(self, *largs):
        pass

    def on_pop(self, *largs):
        pass

    def on_popitem(self, *largs):
        pass

    def on_setdefault(self, *largs):
        pass

    def on_update(self, *largs):
        pass

    def on___delitem__(self, key):
        pass

    def on___setitem__(self, key, value):
        pass


class ObservableDict(ObservableStruct, dict):
    def __init__(
        self,
        parent_prop: ExtendedDictProperty,
        dispatch_on_change_to_prop: bool,
        enable_on_change_only: bool,
        dispatcher: ObservableDictDispatcher,
        *args,
        **kwargs,
    ):
        super().__init__(
            parent_prop,
            dispatch_on_change_to_prop,
            enable_on_change_only,
            dispatcher,
            *args,
            **kwargs,
        )

    @dispatch_on_result
    def clear(self):
        """ObservableDict.clear(self, *largs)"""
        super().clear()

    @dispatch_on_result
    def pop(self, key):
        """ObservableDict.pop(self, *largs)"""
        super().pop(key)

    @dispatch_on_result
    def popitem(self):
        """ObservableDict.popitem(self, *largs)"""
        super().popitem()

    @dispatch_on_result
    def setdefault(self, *largs):
        """ObservableDict.setdefault(self, *largs)"""
        super().setdefault(*largs)

    @dispatch_on_result
    def update(self, *largs):
        """ObservableDict.update(self, *largs)"""
        super().update(*largs)

    @dispatch_on_result
    def __delitem__(self, key):
        """ObservableDict.__delitem__(self, key)"""
        super().__delitem__(key)

    @dispatch_on_result
    def __setitem__(self, key, value):
        """ObservableDict.__setitem__(self, key, value)"""
        super().__setitem__(key, value)


class ExtendedDictProperty(ExtendedStructProperty):
    def __init__(
        self,
        struct_cls=ObservableDict,
        dispatcher=None,
        defaultvalue=None,
        dispatch_on_change_to_prop=True,
        enable_on_change_only=False,
        **kwargs,
    ):
        if defaultvalue is None:
            defaultvalue = dict()

        if dispatcher is None:
            dispatcher = ObservableDictDispatcher()

        super().__init__(
            struct_cls=struct_cls,
            dispatcher=dispatcher,
            defaultvalue=defaultvalue,
            dispatch_on_change_to_prop=dispatch_on_change_to_prop,
            enable_on_change_only=enable_on_change_only,
            **kwargs,
        )
