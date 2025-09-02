# kvx/masks.py
from dataclasses import dataclass
from typing import Protocol


class MaskBehavior(Protocol):
    def render(self, text: str) -> str: ...
    def editable_positions(self) -> list[int]: ...


@dataclass
class PhoneMask(MaskBehavior):
    pattern: str
    placeholder: str = "#"

    def editable_positions(self) -> list[int]:
        return [i for i, ch in enumerate(self.pattern) if ch == self.placeholder]

    def render(self, text: str) -> str:
        digits = [ch for ch in text if ch.isdigit()]
        out: list[str] = []
        di = 0
        for ch in self.pattern:
            if ch == self.placeholder:
                out.append(digits[di] if di < len(digits) else self.placeholder)
                di += 1 if di < len(digits) else 0
            else:
                out.append(ch)
        return "".join(out)
