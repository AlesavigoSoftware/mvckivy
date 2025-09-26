from __future__ import annotations

import logging
from contextlib import suppress
from dataclasses import dataclass
from types import CodeType
from typing import Iterable

from kivy.event import EventDispatcher
from kivy.lang import Builder

from mvckivy.properties.extended_alias_property import ExtendedAliasProperty


logger = logging.getLogger("AliasDedupe")
for name in ("faker", "faker.factory", "faker.providers"):
    logging.getLogger(name).setLevel(logging.WARNING)


@dataclass(slots=True)
class _RuleHit:
    rule_idx: int
    targets: set[str]
    class_rank: int
    uses_alias: bool


class AliasDedupeMixin(EventDispatcher):
    """
    Автодедуп alias-связей, если свойство переопределено правилами «ниже по иерархии».
    Алгоритм:
      1) Builder.match(self) → последовательность ParserRule, применённых к инстансу.
      2) Для каждого свойства определяем все «попадания» (кто когда писал).
      3) Находим последнего писателя; если итоговое выражение **не** использует alias,
         а ранее были писатели через alias_<prop>, то вызываем unbindAll() у alias’а.
    Выполняется один раз в on_kv_post (в текущем кадре).
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_kv_post(self, base_widget) -> None:
        with suppress(AttributeError):
            super().on_kv_post(base_widget)
        try:
            self._alias_dedupe_once()
        except Exception as ex:
            logger.exception("AliasDedupe: cleanup failed\n%r", ex)

    def _alias_dedupe_once(self) -> None:
        rules = Builder.match(self)

        # Построим карту «prop -> список попаданий»
        prop_hits: dict[str, list[_RuleHit]] = {}

        # Предрасчёт: имя класса → ранг по MRO (0 — текущий класс, больше — родители)
        mro_names = [cls.__name__ for cls in type(self).mro()]
        rank: dict[str, int] = {name: idx for idx, name in enumerate(mro_names)}

        for idx, rule in enumerate(rules):
            # Кого таргетит правило
            targets = set(self._split_rule_targets(rule.name))
            # Выбираем «наиболее близкую» к self цель (для сравнения «кто младше/старше»)
            best_rank = min(rank.get(t, 10_000) for t in targets)

            # Свойства правила — dict или list ParserRuleProperty
            for prop_name, prp in self._iter_rule_properties(rule):
                uses_alias = self._rule_prop_uses_alias(prp, prop_name)
                prop_hits.setdefault(prop_name, []).append(
                    _RuleHit(
                        rule_idx=idx,
                        targets=targets,
                        class_rank=best_rank,
                        uses_alias=uses_alias,
                    )
                )

        # Для каждого свойства принимаем решение по alias
        for prop_name, hits in prop_hits.items():
            if len(hits) < 2:
                # не перекрывалось — ничего не делаем
                continue

            last_uses_alias = hits[-1].uses_alias
            if last_uses_alias:
                # финальное значение всё ещё через alias — сохраняем alias
                continue

            had_alias_before = any(h.uses_alias for h in hits[:-1])
            if had_alias_before:
                # По базовому поведению: считаем допустимым снять alias, если итог
                # задаётся не-алиасным выражением (константа/другая логика), т.е.
                # «детское» правило реально перекрывает «родительское» по факту последнего писателя.
                self._unbind_alias_completely(f"alias_{prop_name}")

    # ── Сервис: итерировать свойства ParserRule (dict или list) ──────────────
    @staticmethod
    def _iter_rule_properties(rule) -> Iterable[tuple[str, object]]:
        """
        Нормализованный обход свойств правила:
          - если rule.properties — dict: items()
          - если list: берём .name у каждого ParserRuleProperty
        """
        try:
            props = rule.properties
        except Exception:
            return []

        if isinstance(props, dict):
            for name, prp in props.items():
                yield name, prp
        else:
            # list/tuple of ParserRuleProperty
            for prp in props or []:
                try:
                    name = getattr(prp, "name", None)
                    if name:
                        yield name, prp
                except Exception:
                    continue

    @staticmethod
    def _split_rule_targets(raw: str) -> list[str]:
        """
        "<Child>" -> ["Child"]
        "<Parent, Child>" -> ["Parent", "Child"]
        "<-Button,-ToggleButton>" -> ["Button", "ToggleButton"]
        "Foo@Bar" -> "Foo"
        """
        if not isinstance(raw, str) or len(raw) < 2 or raw[0] != "<" or raw[-1] != ">":
            return []
        body = raw[1:-1]
        out: list[str] = []
        for part in body.split(","):
            name = part.strip()
            if not name:
                continue
            if name.startswith("-"):
                name = name[1:]
            if "@" in name:
                name = name.split("@", 1)[0]
            if name:
                out.append(name)
        return out

    # ── Сервис: распознать, использует ли KV-выражение alias_<prop> ──────────
    @staticmethod
    def _rule_prop_uses_alias(prp, prop_name: str) -> bool:
        alias_token = f"alias_{prop_name}"
        # 1) пробуем «сырой» текст выражения
        raw = getattr(prp, "value", None)
        if isinstance(raw, str):
            if alias_token in raw:
                return True
        # 2) пробуем по «скомпилированному» коду
        co = getattr(prp, "co_value", None)
        if isinstance(co, CodeType):
            if alias_token in (co.co_names or ()):
                return True
        return False

    # ── Снять внутренние бинды alias → deps ──────────────────────────────────
    def _unbind_alias_completely(self, alias_name: str) -> None:
        prop_obj = self.property(alias_name)
        if isinstance(prop_obj, ExtendedAliasProperty):
            prop_obj.unbind_all(self)
