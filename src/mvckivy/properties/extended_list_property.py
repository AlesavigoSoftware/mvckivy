from __future__ import annotations

from mvckivy.properties.base_classes import (
    ExtendedStructProperty,
    ObservableStruct,
    dispatch_on_result,
    ObservableStructDispatcher,
)


class ObservableListDispatcher(ObservableStructDispatcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_append")
        self.register_event_type("on_extend")
        self.register_event_type("on_insert")
        self.register_event_type("on_pop")
        self.register_event_type("on_remove")
        self.register_event_type("on_reverse")
        self.register_event_type("on_sort")
        self.register_event_type("on___delitem__")
        self.register_event_type("on___iadd__")
        self.register_event_type("on___imul__")
        self.register_event_type("on___setitem__")

    def on_append(self, *largs):
        pass

    def on_extend(self, *largs):
        pass

    def on_insert(self, i, x):
        pass

    def on_pop(self, *largs):
        pass

    def on_remove(self, *largs):
        pass

    def on_reverse(self, *largs):
        pass

    def on_sort(self, *largs, **kwargs):
        pass

    def on___delitem__(self, key):
        pass

    def on___iadd__(self, *largs):
        pass

    def on___imul__(self, b):
        pass

    def on___setitem__(self, key, value):
        pass


class ObservableList(ObservableStruct, list):
    def __init__(
        self,
        parent_prop: ExtendedListProperty,
        dispatch_on_change_to_prop: bool,
        enable_on_change_only: bool,
        dispatcher: ObservableListDispatcher,
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
    def append(self, *largs):
        """ObservableList.append(self, *largs)"""
        super().append(*largs)

    @dispatch_on_result
    def extend(self, *largs):
        """ObservableList.extend(self, *largs)"""
        super().extend(*largs)

    @dispatch_on_result
    def insert(self, i, x):
        """ObservableList.insert(self, i, x)"""
        super().insert(i, x)

    @dispatch_on_result
    def pop(self, *largs):
        """ObservableList.pop(self, *largs)"""
        super().pop(*largs)

    @dispatch_on_result
    def remove(self, *largs):
        """ObservableList.remove(self, *largs)"""
        super().remove(*largs)

    @dispatch_on_result
    def reverse(self, *largs):
        """ObservableList.reverse(self, *largs)"""
        super().reverse()

    @dispatch_on_result
    def sort(self, *largs, **kwargs):
        """ObservableList.sort(self, *largs, **kwargs)"""
        super().sort(*largs, **kwargs)

    @dispatch_on_result
    def __delitem__(self, key):
        """ObservableList.__delitem__(self, key)"""
        super().__delitem__(key)

    @dispatch_on_result
    def __iadd__(self, *largs):
        """ObservableList.__iadd__(self, *largs)"""
        super().__iadd__(*largs)

    @dispatch_on_result
    def __imul__(self, b):
        """ObservableList.__imul__(self, b)"""
        super().__imul__(b)

    @dispatch_on_result
    def __setitem__(self, key, value):
        """ObservableList.__setitem__(self, key, value)"""
        super().__setitem__(key, value)


class ExtendedListProperty(ExtendedStructProperty):
    def __init__(
        self,
        struct_cls=ObservableList,
        dispatcher=ObservableListDispatcher(),
        defaultvalue=list(),
        dispatch_on_change_to_prop=True,
        enable_on_change_only=False,
        **kwargs,
    ):
        super().__init__(
            struct_cls=struct_cls,
            dispatcher=dispatcher,
            defaultvalue=defaultvalue,
            dispatch_on_change_to_prop=dispatch_on_change_to_prop,
            enable_on_change_only=enable_on_change_only,
            **kwargs,
        )
