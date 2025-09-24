from __future__ import annotations

import logging
import sys
from typing import Iterable, Sequence, List, Tuple

from kivy.clock import Clock
from kivy.event import EventDispatcher

logger = logging.getLogger("mvckivy")

# Тип наблюдателя из get_property_observers(args=True)
Observer = Tuple[callable, tuple, dict, bool, int]


# --------------------------- Утилиты наблюдателей ---------------------------


def list_observers(obj: EventDispatcher, name: str) -> List[Observer]:
    """Вернуть список наблюдателей (cb, largs, kwargs, is_ref, uid) для свойства name."""
    # Прямой вызов метода у self-объекта, без getattr-цепочек.
    return obj.get_property_observers(name, args=True)


def dump_observers(obj: EventDispatcher, names: Sequence[str], title: str = "") -> None:
    if title:
        logger.debug("=== %s ===", title)
    for name in names:
        try:
            for cb, largs, kwargs, is_ref, uid in list_observers(obj, name):
                code = getattr(cb, "__code__", None)
                if code is not None:
                    origin = f"{code.co_filename}:{code.co_firstlineno}"
                    cb_name = getattr(cb, "__name__", repr(cb))
                else:
                    origin = "<native>"
                    cb_name = repr(cb)
                logger.debug(
                    "prop=%-18s uid=%4s  %s  %s", name, str(uid), origin, cb_name
                )
        except Exception as e:
            logger.debug("prop=%s <error listing observers: %r>", name, e)
    sys.stdout.flush()


# --------------------------- Распознавание KV-кода ---------------------------


def is_kv_source(
    cb: callable,
    allow_any_kv_file: bool = True,
    allow_inline: bool = True,
    extra_files: Sequence[str] = (),
) -> bool:
    """
    Колбэк порождён KV, если:
      - файл == "<string>" (Builder.load_*), или
      - файл оканчивается на '.kv', или
      - явно разрешён в extra_files.
    """
    code = getattr(cb, "__code__", None)
    if code is None:
        return False
    fn = code.co_filename
    if allow_inline and fn == "<string>":
        return True
    if allow_any_kv_file and isinstance(fn, str) and fn.lower().endswith(".kv"):
        return True
    if extra_files:
        extra = set(extra_files)
        if fn in extra:
            return True
    return False


def observer_mentions_target(
    cb: callable, largs: tuple, kwargs: dict, target_prop: str
) -> bool:
    """
    Эвристики: имя целевого свойства встретилось либо в аргументах наблюдателя (редко),
    либо в именных константах/именах кода (чаще).
    """
    # Аргументы (редко пригодно, но оставим как быстрый путь)
    try:
        if any((isinstance(a, str) and a == target_prop) for a in (largs or ())):
            return True
        if any(
            (isinstance(v, str) and v == target_prop) for v in (kwargs or {}).values()
        ):
            return True
    except Exception:
        pass

    # По коду (чаще встречается у KV-генерируемых колбэков)
    code = getattr(cb, "__code__", None)
    if code is None:
        return False
    names = set(getattr(code, "co_names", ()))
    consts = {c for c in getattr(code, "co_consts", ()) if isinstance(c, str)}
    return (target_prop in names) or (target_prop in consts)


def iter_observable_names(obj: EventDispatcher) -> Iterable[str]:
    """Все имена свойств объекта, у которых вообще бывают наблюдатели."""
    return obj.properties().keys()


# --------------------------- Дедуп целевого свойства ---------------------------


def collect_kv_observers_for_target(
    obj: EventDispatcher,
    target_prop: str,
    *,
    include_target_prop: bool = True,
    kv_inline_ok: bool = True,
    kv_anyfile_ok: bool = True,
    kv_extra_files: Sequence[str] = (),
) -> List[Tuple[str, int, callable]]:
    """
    Собрать **единый список** KV-наблюдателей, которые **пишут** в target_prop,
    по всем наблюдаемым свойствам obj (включая target_prop при необходимости).

    Возвращает список: (observed_prop, uid, cb)
    """
    result: List[Tuple[str, int, callable]] = []
    for observed_prop in iter_observable_names(obj):
        if not include_target_prop and observed_prop == target_prop:
            continue

        for cb, largs, kwargs, is_ref, uid in list_observers(obj, observed_prop):
            if not uid:
                continue
            if not is_kv_source(cb, kv_anyfile_ok, kv_inline_ok, kv_extra_files):
                continue
            if not observer_mentions_target(cb, largs, kwargs, target_prop):
                continue
            result.append((observed_prop, uid, cb))
    return result


def dedupe_target(
    obj: EventDispatcher,
    target_prop: str,
    *,
    keep_latest: bool = True,
    kv_inline_ok: bool = True,
    kv_anyfile_ok: bool = True,
    kv_extra_files: Sequence[str] = (),
) -> int:
    """
    Снять KV-наблюдателей, **которые пишут в target_prop**.

    По умолчанию оставляет **только самый поздний** (максимальный uid) среди всех
    KV-наблюдателей, которые писали в target_prop; остальные снимает.
    Если keep_latest=False — снимает **всех** таких наблюдателей.
    """
    # ВАЖНО: собираем одним списком по *всем* observed_prop (и включая target_prop)
    kv_obs = collect_kv_observers_for_target(
        obj,
        target_prop,
        include_target_prop=True,  # НЕ игнорируем target_prop
        kv_inline_ok=kv_inline_ok,
        kv_anyfile_ok=kv_anyfile_ok,
        kv_extra_files=kv_extra_files,
    )
    if not kv_obs:
        return 0

    # Сортировка по uid (uid растёт с регистрацией) — глобальный порядок
    kv_obs.sort(key=lambda item: item[1])  # item = (observed_prop, uid, cb)

    to_remove: List[Tuple[str, int]] = []
    if keep_latest:
        # Оставляем последний по uid, остальные помечаем на снятие
        for observed_prop, uid, _ in kv_obs[:-1]:
            to_remove.append((observed_prop, uid))
    else:
        # Снимаем всех
        for observed_prop, uid, _ in kv_obs:
            to_remove.append((observed_prop, uid))

    removed = 0
    for observed_prop, uid in to_remove:
        try:
            obj.unbind_uid(observed_prop, uid)
            removed += 1
        except Exception:
            # молча, чтобы не мешать тестам/рантайму
            pass
    return removed


# --------------------------- Примесь для виджетов ---------------------------


class KVDedupeMixin:
    """
    __kv_dedupe_targets__ — кортеж имён свойств (например, ("padding",))
    __kv_keep_latest__    — True: оставить один «самый поздний» KV-биндинг в target;
                            False: снять все KV-биндинги, пишущие в target.
    __kv_allow_inline__   — учитывать KV из Builder.load_string (файл "<string>")
    __kv_allow_any_kv_file__ — учитывать любые *.kv файлы
    __kv_extra_files__    — явный whitelist файлов, которые считать KV-источником
    """

    __kv_dedupe_targets__: Sequence[str] = ()
    __kv_keep_latest__: bool = True

    __kv_allow_inline__: bool = True
    __kv_allow_any_kv_file__: bool = True
    __kv_extra_files__: Sequence[str] = ()

    def on_kv_post(self, base_widget):
        # Никаких getattr: прямой вызов super, если есть у MRO
        try:
            super().on_kv_post(base_widget)  # type: ignore[misc]
        except AttributeError:
            pass

        if not self.__kv_dedupe_targets__:
            return

        def _run(_dt: float) -> None:
            observed_snapshot = tuple(sorted(iter_observable_names(self)))
            dump_observers(self, observed_snapshot, "до GLOBAL-dedupe")

            total_removed = 0
            for target_prop in self.__kv_dedupe_targets__:
                total_removed += dedupe_target(
                    self,
                    target_prop,
                    keep_latest=self.__kv_keep_latest__,
                    kv_inline_ok=self.__kv_allow_inline__,
                    kv_anyfile_ok=self.__kv_allow_any_kv_file__,
                    kv_extra_files=self.__kv_extra_files__,
                )

            dump_observers(
                self, observed_snapshot, f"после GLOBAL-dedupe (снято {total_removed})"
            )

        # Следующий кадр — чтобы гарантированно увидеть ВСЕ KV-правила (и от предка, и от наследника)
        Clock.schedule_once(_run, 0)
