from __future__ import annotations

import logging
from typing import Sequence, Iterable
import sys

from kivy.clock import Clock
from kivy.event import EventDispatcher


logger = logging.getLogger("mvckivy")


def list_observers(obj: EventDispatcher, name: str):
    """Вернуть список наблюдателей: (cb, largs, kwargs, is_ref, uid)."""
    return obj.get_property_observers(name, args=True)


def dump_observers(obj: EventDispatcher, names: Sequence[str], title: str = ""):
    for name in names:
        for cb, largs, kwargs, is_ref, uid in list_observers(obj, name):
            code = getattr(cb, "__code__", None)
            if code is not None:
                origin = f"{code.co_filename}:{code.co_firstlineno}"
                cb_name = getattr(cb, "__name__", repr(cb))
            else:
                origin = "<native>"
                cb_name = repr(cb)
            logger.debug(f"uid={uid!s:>4}  {origin}  {cb_name}")
    sys.stdout.flush()


def _is_kv_source(
    cb,
    allow_any_kv_file: bool = True,
    allow_inline: bool = True,
    extra_files: Sequence[str] = (),
):
    """Оставляем колбэки из .kv или <string> (Builder.load_*)."""
    code = getattr(cb, "__code__", None)
    if code is None:
        return False
    fn = code.co_filename
    if allow_inline and fn == "<string>":
        return True
    if allow_any_kv_file and isinstance(fn, str) and fn.lower().endswith(".kv"):
        return True
    if extra_files and fn in set(extra_files):
        return True
    return False


def _observer_targets_prop_by_args(largs, kwargs, target_prop: str) -> bool:
    try:
        if any(isinstance(a, str) and a == target_prop for a in (largs or ())):
            return True
        if any(
            isinstance(v, str) and v == target_prop for v in (kwargs or {}).values()
        ):
            return True
    except Exception:
        pass
    return False


def _cb_targets_property(cb, largs, kwargs, target_prop: str) -> bool:
    if _observer_targets_prop_by_args(largs, kwargs, target_prop):
        return True
    code = getattr(cb, "__code__", None)
    if code is not None:
        names = set(getattr(code, "co_names", ()))
        consts = {c for c in getattr(code, "co_consts", ()) if isinstance(c, str)}
        if target_prop in names or target_prop in consts:
            return True
    return False


def iter_all_observable_names(obj: EventDispatcher) -> Iterable[str]:
    """Все имена свойств объекта, поддерживающих наблюдателей."""
    return obj.properties().keys()


# -------------------- Глобальный дедуп по целевому свойству --------------------
def dedupe_target_globally(
    obj: EventDispatcher,
    target_prop: str,
    *,
    keep_latest: bool = True,
    kv_inline_ok: bool = True,
    kv_anyfile_ok: bool = True,
    kv_extra_files: Sequence[str] = (),
) -> int:
    """
    На ВСЕХ свойствах obj снимаем KV-бинды, которые пишут в target_prop.
    keep_latest=True — оставить последний (override), снять старые.
    keep_latest=False — снять все.
    """
    removed_total = 0
    for observed_prop in iter_all_observable_names(obj):
        if observed_prop == target_prop:  # не трогаем слушателей самого свойства
            continue
        obs = list_observers(obj, observed_prop)
        kv_obs = [
            (cb, uid, largs, kwargs)
            for (cb, largs, kwargs, is_ref, uid) in obs
            if uid
            and _is_kv_source(cb, kv_anyfile_ok, kv_inline_ok, kv_extra_files)
            and _cb_targets_property(cb, largs, kwargs, target_prop)
        ]
        if not kv_obs:
            continue

        if keep_latest:
            for cb, uid, largs, kwargs in kv_obs[:-1]:
                try:
                    obj.unbind_uid(observed_prop, uid)
                    removed_total += 1
                except Exception:
                    pass
        else:
            for cb, uid, largs, kwargs in kv_obs:
                try:
                    obj.unbind_uid(observed_prop, uid)
                    removed_total += 1
                except Exception:
                    pass
    return removed_total


class KVDedupeGlobalMixin:
    """
    __kv_dedupe_targets__ — список целевых свойств для глобальной очистки.
    __kv_keep_latest__   — True: оставить последний (override), иначе снять все.
    """

    __kv_dedupe_targets__: Sequence[str] = ()
    __kv_keep_latest__: bool = True

    __kv_allow_inline__: bool = True
    __kv_allow_any_kv_file__: bool = True
    __kv_extra_files__: Sequence[str] = ()

    def on_kv_post(self, base_widget):
        sup = getattr(super(), "on_kv_post", None)
        if callable(sup):
            sup(base_widget)

        if not self.__kv_dedupe_targets__:
            return

        def _run(_dt):
            observed_snapshot = tuple(sorted(iter_all_observable_names(self)))
            dump_observers(self, observed_snapshot, "до GLOBAL-dedupe")

            total = 0
            for target_prop in self.__kv_dedupe_targets__:
                total += dedupe_target_globally(
                    self,
                    target_prop,
                    keep_latest=self.__kv_keep_latest__,
                    kv_inline_ok=self.__kv_allow_inline__,
                    kv_anyfile_ok=self.__kv_allow_any_kv_file__,
                    kv_extra_files=self.__kv_extra_files__,
                )

            dump_observers(
                self, observed_snapshot, f"после GLOBAL-dedupe (снято {total})"
            )

        # следующий кадр — чтобы гарантированно захватить правила наследника
        Clock.schedule_once(_run, 0)
