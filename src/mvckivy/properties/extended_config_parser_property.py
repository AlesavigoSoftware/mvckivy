from __future__ import annotations

import json
from typing import Union, Iterable, Any, Mapping

from kivy.properties import ConfigParserProperty

from .base_classes import ObserversCollectorMixin


class ExtendedConfigParserProperty(ObserversCollectorMixin, ConfigParserProperty):
    def __init__(self, defaultvalue: Any, section: str, key: str, config: str, val_type: Any = str, **kw):
        super().__init__(defaultvalue, section, key, config, val_type=val_type, **kw)

        if val_type is ConfigParserList or val_type is ConfigParserDict:
            val_type.set_parent_config(self, section, key)


class PropertyWrongNameException(Exception):
    pass


class ConfigParserDict(dict):
    _parent_config: list[ExtendedConfigParserProperty, str, str] = []

    def __init__(
            self,
            init_value: Union[Iterable, str, None] = None,
    ):
        if isinstance(init_value, str):
            super().__init__(json.loads(init_value.replace('\'', '"')))
        elif isinstance(init_value, Iterable) or isinstance(init_value, Mapping):
            super().__init__(init_value)
        elif init_value is None:
            super().__init__()

    @classmethod
    def set_parent_config(cls, parent_prop: ExtendedConfigParserProperty, section: str, key: str):
        cls._parent_config.extend([parent_prop, section, key])

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        prop, section, key = self._parent_config
        prop._edit_setting(section, key, str(self))  # dispatches prop to all observers


class ConfigParserList(list):
    _parent_config: list[ExtendedConfigParserProperty, str, str] = []

    def __init__(
            self,
            init_value: Union[Iterable, str, None] = None,
    ):
        if isinstance(init_value, str):
            super().__init__(json.loads(init_value.replace('\'', '"')))
        elif isinstance(init_value, Iterable):
            super().__init__(init_value)
        elif init_value is None:
            super().__init__()

    @classmethod
    def set_parent_config(cls, parent_prop: ExtendedConfigParserProperty, section: str, key: str):
        cls._parent_config.extend([parent_prop, section, key])

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        prop, section, key = self._parent_config

        # for name, observer in prop.bound_observers.items():
        #     prop.dispatch(observer)  # doubles dispatch

        prop._edit_setting(section, key, str(self))  # dispatches prop to all observers


class ConfigParserBool:
    def __init__(self, value):
        if isinstance(value, str):
            value = value.strip()

            if value == 'False':
                self._value = False
            elif value == 'True':
                self._value = True
            else:
                self._value = bool(value)
        else:
            self._value = bool(value)

    def __repr__(self):
        return repr(self._value)

    def __str__(self):
        return str(self._value)

    def __bool__(self):
        return self._value

    def __eq__(self, other):
        return self._value == bool(other)

    def __ne__(self, other):
        return self._value != bool(other)

    def __and__(self, other):
        return ConfigParserBool(self._value and bool(other))

    def __or__(self, other):
        return ConfigParserBool(self._value or bool(other))

    def __xor__(self, other):
        return ConfigParserBool(self._value ^ bool(other))

    def __invert__(self):
        return ConfigParserBool(not self._value)

    def __hash__(self):
        return hash(self._value)

    def __int__(self):
        return int(self._value)
