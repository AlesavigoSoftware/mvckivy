from dataclasses import dataclass, field
from typing import Any, Iterable
from datetime import datetime, date
import ipaddress
import importlib
import re


class ValidatorBehavior:
    def validate(self, text: str) -> bool:
        raise NotImplementedError


@dataclass
class ValidatorResolver:
    aliases: dict[str, type[ValidatorBehavior]] = field(default_factory=dict)

    def register(self, name: str, cls: type[ValidatorBehavior]) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("alias name must be non-empty str")
        if not isinstance(cls, type) or not issubclass(cls, ValidatorBehavior):
            raise TypeError("cls must be subclass of ValidatorBehavior")
        self.aliases[name] = cls

    def resolve_class(self, name: str) -> type[ValidatorBehavior]:
        if name in self.aliases:
            return self.aliases[name]
        module_name = None
        class_name = None
        if ":" in name:
            module_name, class_name = name.split(":", 1)
        elif "." in name:
            parts = name.split(".")
            module_name, class_name = ".".join(parts[:-1]), parts[-1]
        if module_name and class_name:
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            if not issubclass(cls, ValidatorBehavior):
                raise TypeError(f"{cls} is not a ValidatorBehavior")
            return cls
        raise KeyError(f"Unknown validator '{name}'")

    def create(
        self, spec: str | dict | type[ValidatorBehavior] | ValidatorBehavior
    ) -> ValidatorBehavior:
        if isinstance(spec, ValidatorBehavior):
            return spec
        if isinstance(spec, type) and issubclass(spec, ValidatorBehavior):
            return spec()
        if isinstance(spec, str):
            cls = self.resolve_class(spec)
            return cls()
        if isinstance(spec, dict):
            name = spec.get("name")
            if not isinstance(name, str):
                raise ValueError("spec must include 'name'")
            params = {k: v for k, v in spec.items() if k != "name"}
            cls = self.resolve_class(name)
            return cls(**params)
        raise TypeError("Unsupported validator spec")

    def create_many(self, specs: Iterable[Any]) -> list[ValidatorBehavior]:
        return [self.create(s) for s in specs]


_EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


@dataclass
class EmailValidator(ValidatorBehavior):
    def validate(self, text: str) -> bool:
        return bool(_EMAIL_REGEX.match(text))


@dataclass
class IPValidator(ValidatorBehavior):
    def validate(self, text: str) -> bool:
        try:
            ipaddress.ip_address(text)
            return True
        except ValueError:
            return False


@dataclass
class PhoneValidator(ValidatorBehavior):
    min_digits: int = 10
    max_digits: int = 15

    def validate(self, text: str) -> bool:
        digits = "".join(ch for ch in text if ch.isdigit())
        return self.min_digits <= len(digits) <= self.max_digits


@dataclass
class DateValidator(ValidatorBehavior):
    format: str = "%Y-%m-%d"
    min: str | None = None
    max: str | None = None

    def _parse(self, s: str) -> date:
        return datetime.strptime(s, self.format).date()

    def validate(self, text: str) -> bool:
        try:
            d = self._parse(text)
        except Exception:
            return False
        if self.min is not None:
            try:
                if d < self._parse(self.min):
                    return False
            except Exception:
                return False
        if self.max is not None:
            try:
                if d > self._parse(self.max):
                    return False
            except Exception:
                return False
        return True


@dataclass
class DateRangeValidator(ValidatorBehavior):
    format: str = "%Y-%m-%d"
    sep: str = ".."

    def _parse(self, s: str) -> date:
        return datetime.strptime(s, self.format).date()

    def validate(self, text: str) -> bool:
        try:
            a, b = text.split(self.sep, 1)
            d1, d2 = self._parse(a.strip()), self._parse(b.strip())
            return d1 <= d2
        except Exception:
            return False


@dataclass
class TimeValidator(ValidatorBehavior):
    format: str = "%H:%M"

    def validate(self, text: str) -> bool:
        try:
            datetime.strptime(text, self.format).time()
            return True
        except Exception:
            return False
