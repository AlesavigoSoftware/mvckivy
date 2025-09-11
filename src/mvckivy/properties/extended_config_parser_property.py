from __future__ import annotations

import json
from contextlib import suppress
from functools import partial
from typing import Iterable, Any, Type, Callable, TypeVar

from kivy.properties import ConfigParserProperty
from kivy.weakproxy import WeakProxy


class ExtendedConfigParserProperty(ConfigParserProperty):
    def __init__(
        self,
        defaultvalue: Any,
        section: str,
        key: str,
        config: str,
        val_type: Type[Any] = str,
        validators: Iterable[Validator] = (),
        options: Iterable = (),
        **kw,
    ):
        self.options = options
        self.validators = validators

        super().__init__(
            defaultvalue,
            section,
            key,
            config,
            val_type=self._val_type(
                val_type,
                parent_property=WeakProxy(self),
                validators=validators,
                options=options,
            ),
            **kw,
        )

    @staticmethod
    def _val_type(val_type: Type[Any], **kwargs) -> Callable[[Any], Any]:

        if issubclass(val_type, ConfigParserString):
            validators = (
                *kwargs.pop("validators"),
                OptionsValidator(kwargs.pop("options")),
            )
            val_type = partial(val_type, validators=validators, **kwargs)

        elif issubclass(val_type, ConfigParserValueTypeMixin):
            val_type = partial(val_type, **kwargs)

        return val_type

    def set_setting(self, section: str, key: str, value: Any):
        self._edit_setting(section, key, value)


class PropertyWrongNameException(Exception):
    pass


class Validator:
    def validate(self, value) -> bool:
        raise NotImplementedError()


class OptionsValidator(Validator):
    def __init__(self, options: Iterable):
        self.options = set(options)

    def validate(self, value) -> bool:
        return value in self.options if self.options else True


T = TypeVar("T")


class ConfigParserValueTypeMixin:
    def __init__(
        self,
        *args,
        parent_property: WeakProxy[ExtendedConfigParserProperty] = None,
        validators: Iterable[Validator] = (),
        section: str = "",
        key: str = "",
        **kwargs,
    ):
        self._parent_property = parent_property
        self._section = section
        self._key = key
        self._validators = validators

        with suppress(KeyError, TypeError):
            super().__init__(*args, **kwargs)

    def _validate(self, value: T) -> T:
        for validator in self._validators:
            if not validator.validate(value):
                raise ValueError(
                    f"Validation failed for value: {value}. Validator: {validator}"
                )

        return value

    def set_setting(self, section: str, key: str):
        if self._parent_property is None:
            raise PropertyWrongNameException(
                "Parent property is not set for this value type."
            )
        self._parent_property.set_setting(section, key, self.str())

    def str(self):
        return str(self)


class ConfigParserMappingTypeMixin(ConfigParserValueTypeMixin):
    def __init__(
        self,
        init_value: Iterable | str | None = None,
        parent_property: WeakProxy[ExtendedConfigParserProperty] = None,
        validators: Iterable[Validator] = (),
        section: str = "",
        key: str = "",
    ):
        if init_value is None:
            super().__init__(
                parent_property=parent_property,
                validators=validators,
                section=section,
                key=key,
            )
        else:
            super().__init__(
                self._format_and_validate_value(init_value),
                parent_property=parent_property,
                validators=validators,
                section=section,
                key=key,
            )

    def _format_and_validate_value(self, value: Iterable | str) -> Iterable:
        if isinstance(value, str):
            value = json.loads(value.replace("'", '"'))
        return self._validate(value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.set_setting(self._section, self._key)


class ConfigParserDict(ConfigParserValueTypeMixin, dict):
    pass


class ConfigParserList(ConfigParserMappingTypeMixin, list):
    pass


class ConfigParserBool(ConfigParserValueTypeMixin):
    def __init__(
        self,
        init_value: Iterable | str | None,
        parent_property: WeakProxy[ExtendedConfigParserProperty] = None,
        validators: Iterable[Validator] = (),
        section: str = "",
        key: str = "",
    ):
        super().__init__(
            init_value,
            parent_property=parent_property,
            validators=validators,
            section=section,
            key=key,
        )
        self._value: bool = self._format_value(init_value)

    @staticmethod
    def _format_value(value: str | bool) -> bool:

        if isinstance(value, str):
            value = value.strip()
            if value in ["False", "false", "0", "None", "null", ""]:
                return False
            elif value in ["True", "true", "1"]:
                return True

        return bool(value)

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
        return self._value and bool(other)

    def __or__(self, other):
        return self._value or bool(other)

    def __xor__(self, other):
        return self._value ^ bool(other)

    def __invert__(self):
        return not self._value

    def __hash__(self):
        return hash(self._value)

    def __int__(self):
        return int(self._value)


class ConfigParserString(ConfigParserValueTypeMixin, str):
    def __init__(
        self,
        init_value: str | None,
        parent_property: WeakProxy[ExtendedConfigParserProperty] = None,
        validators: Iterable[Validator] = (),
        section: str = "",
        key: str = "",
    ):
        if init_value is None:
            super().__init__(
                parent_property=parent_property,
                validators=validators,
                section=section,
                key=key,
            )
        else:
            super().__init__(
                self._format_and_validate_value(init_value),
                parent_property=parent_property,
                validators=validators,
                section=section,
                key=key,
            )

    def _format_and_validate_value(self, value: str) -> str:
        return self._validate(value.strip())
