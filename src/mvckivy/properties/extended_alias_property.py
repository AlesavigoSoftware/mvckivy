from __future__ import annotations

from functools import partial
from typing import Any, Sequence
import weakref

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty
from kivy.weakproxy import WeakProxy


class ExtendedAliasProperty(AliasProperty):
    """
    Расширенный AliasProperty с поддержкой:
      • зависимостей по точечным путям ('a.b.c'),
      • строгого rebind промежуточных узлов (по флагу rebind у Property),
      • отложенного перелинковывания цепочек (Clock),
      • слабых ссылок (WeakProxy/weakref),
      • отслеживания «причины» изменения (last_cause),
      • полного снятия подписок (unbind_all / dispose).

    Семантика watch_before_use:
      True  — связать зависимости заранее (eager) при создании хранилища (link_eagerly).
      False — лениво связывать при первом взаимодействии (get/set/bind).
    """

    # ---------- Конструктор и публичный API (в порядке вызова) ----------

    def __init__(
        self,
        getter,
        setter=None,
        *,
        bind: Sequence[str] = (),
        cache: bool = False,
        watch_before_use: bool = True,
        respect_rebind_flag: bool = True,
        **kwargs: Any,
    ) -> None:
        self._user_getter = getter
        self._user_setter = setter
        self._bind_names: tuple[str, ...] = tuple(bind)
        self._respect_rebind_flag = bool(respect_rebind_flag)
        self._watch_before_use = bool(watch_before_use)

        sid = id(self)
        self._linked_key = f"__ap_linked_{sid}"
        self._cause_key = f"__ap_cause_{sid}"
        self._uids_key = f"__ap_uids_{sid}"  # list[(ref_or_obj, name, uid)]
        self._chains_key = f"__ap_chains_{sid}"  # path -> list[(ref_or_obj, name, uid)]
        self._triggers_key = f"__ap_triggers_{sid}"  # path -> ClockEvent
        self._sig_key = f"__ap_sig_{sid}"  # path -> tuple(signature)

        # Внутренние bind'ы AliasProperty отключаем — биндим зависимости сами.
        super().__init__(
            lambda obj: getter(obj, self),
            (lambda obj, value: setter(obj, value, self)) if setter else None,
            bind=(),
            cache=cache,
            watch_before_use=self._watch_before_use,
            **kwargs,
        )

    def last_cause(self, obj: EventDispatcher) -> str | None:
        """Вернуть последнюю «причину» вида 'a', 'a.b', 'a.b.c'."""
        return getattr(obj, self._cause_key, None)

    def unbind_all(self, obj: EventDispatcher) -> None:
        """Снять все слушатели зависимостей и очистить служебное состояние."""
        self.dispose(obj)

    def dispose(self, obj: EventDispatcher) -> None:
        """Полностью убрать подписки (простые и цепочки), отменить триггеры, сбросить кэши."""
        for ref_or_obj, name, uid in list(self._get_uid_list(obj)):
            disp = self._deref(ref_or_obj)
            if disp is not None:
                self._unbind_by_uid(disp, name, uid)
        setattr(obj, self._uids_key, [])

        for bundle in list(self._get_chains_map(obj).values()):
            for ref_or_obj, name, uid in bundle:
                disp = self._deref(ref_or_obj)
                if disp is not None:
                    self._unbind_by_uid(disp, name, uid)

        setattr(obj, self._chains_key, {})
        setattr(obj, self._sig_key, {})
        setattr(obj, self._linked_key, False)
        setattr(obj, self._cause_key, None)

    # ---------- Интеграция с жизненным циклом Kivy.Property ----------

    def link_eagerly(self, obj: EventDispatcher):
        """Раннее связывание зависимостей, если watch_before_use=True."""
        if self._watch_before_use:
            self._ensure_dependencies_linked(obj)
        return super().link_eagerly(obj)

    def link_deps(self, obj: EventDispatcher, unicode_name: str):
        """Связывание при bind на сам алиас (первое использование)."""
        self._ensure_dependencies_linked(obj)
        return super().link_deps(obj, unicode_name)

    def get(self, obj: EventDispatcher):
        """Ленивое связывание при первом чтении (если watch_before_use=False)."""
        if not self._watch_before_use or not getattr(obj, self._linked_key, False):
            self._ensure_dependencies_linked(obj)
        return super().get(obj)

    def set(self, obj: EventDispatcher, value: Any):
        """Ленивое связывание при первой записи (если watch_before_use=False)."""
        if not self._watch_before_use or not getattr(obj, self._linked_key, False):
            self._ensure_dependencies_linked(obj)
        return super().set(obj, value)

    # ---------- Логика связывания и перелинковки зависимостей ----------

    def _ensure_dependencies_linked(self, obj: EventDispatcher) -> None:
        """Установить слушатели для всех зависимостей (простых и по цепочкам), если ещё не связаны."""
        if getattr(obj, self._linked_key, False):
            return

        uids = self._get_uid_list(obj)
        owner_ref = self._weak_ref(obj)

        def bind_simple(prop_name: str, label: str) -> None:
            cb = partial(self._on_dependency_changed, label, owner_ref)
            uid = obj.fbind(prop_name, cb)
            if uid:
                uids.append((self._weak_ref(obj), prop_name, uid))

        for name in self._bind_names:
            if "." in name:
                self._link_dependency_chain(obj, name, defer=False)
            else:
                bind_simple(name, name)

        setattr(obj, self._linked_key, True)

    def _make_chain_relink(self, root_obj: EventDispatcher, path: str) -> None:
        owner_ref = self._weak_ref(root_obj)
        owner = self._deref(owner_ref)
        if owner is not None:
            self._link_dependency_chain(owner, path, defer=False)

    def _calculate_chain_signature(
        self, root_obj: EventDispatcher, path: str
    ) -> tuple[int, ...]:
        """
        Подпись цепочки — последовательность id диспетчеров по сегментам.
        Нужна, чтобы не перестраивать неизменённые цепочки.
        """
        segs = path.split(".")
        disp: Any = root_obj
        signature: list[int] = []
        for idx, seg in enumerate(segs):
            if not isinstance(disp, EventDispatcher):
                signature.append(0)
                break
            try:
                disp.property(seg, quiet=True)
            except Exception:
                pass
            signature.append(id(disp))
            if idx < len(segs) - 1:
                try:
                    disp = getattr(disp, seg)
                except Exception:
                    disp = None
        return tuple(signature)

    def _link_dependency_chain(
        self, root_obj: EventDispatcher, path: str, *, defer: bool
    ) -> None:
        """Построить слушатели для dotted-цепочки вида 'a.b.c'."""
        if defer:
            self._make_chain_relink(root_obj, path)
            return

        signatures = self._get_signatures_map(root_obj)
        new_sig = self._calculate_chain_signature(root_obj, path)
        if signatures.get(path) == new_sig:
            return
        signatures[path] = new_sig

        self._unlink_dependency_chain(root_obj, path)

        chains = self._get_chains_map(root_obj)
        segs = path.split(".")
        disp: Any = root_obj
        watchers: list[tuple[Any, str, int]] = []
        owner_ref = self._weak_ref(root_obj)

        def fbind_and_track(d: EventDispatcher, prop: str, cb) -> None:
            uid = d.fbind(prop, cb)
            if uid:
                watchers.append((self._weak_ref(d), prop, uid))

        def should_rebind_node(d: EventDispatcher, prop: str) -> bool:
            if not self._respect_rebind_flag:
                return True
            try:
                p = d.property(prop, quiet=True)
            except Exception:
                p = None
            return bool(getattr(p, "rebind", False)) if p is not None else False

        for idx, seg in enumerate(segs):
            if not isinstance(disp, EventDispatcher):
                break

            is_leaf = idx == len(segs) - 1
            if is_leaf:
                cb = partial(self._on_dependency_changed, path, owner_ref)
                fbind_and_track(disp, seg, cb)
            else:
                prefix_idx = idx

                def on_node_change(
                    inst: EventDispatcher, value: Any, _idx=prefix_idx, _seg=seg
                ) -> None:
                    owner = self._deref(owner_ref)
                    if owner is None:
                        return
                    setattr(owner, self._cause_key, ".".join(segs[: _idx + 1]))
                    if should_rebind_node(inst, _seg):
                        self._make_chain_relink(owner, path)
                    new_val = self._user_getter(owner, self)
                    super(ExtendedAliasProperty, self).trigger_change(owner, new_val)

                fbind_and_track(disp, seg, on_node_change)
                try:
                    disp = getattr(disp, seg)
                except Exception:
                    disp = None

        chains[path] = watchers

    def _unlink_dependency_chain(self, root_obj: EventDispatcher, path: str) -> None:
        """Снять все слушатели, связанные с конкретной цепочкой."""
        chains = self._get_chains_map(root_obj)
        old = chains.pop(path, None)
        if not old:
            return
        for ref_or_obj, name, uid in old:
            disp = self._deref(ref_or_obj)
            if disp is not None:
                self._unbind_by_uid(disp, name, uid)

    # ---------- Колбэк изменений и утилиты низкого уровня ----------

    def _on_dependency_changed(
        self, label: str, owner_ref, _inst: EventDispatcher, _value: Any
    ) -> None:
        """Общий колбэк для всех зависимостей: сохранить причину и задиспатчить новое значение."""
        owner = self._deref(owner_ref)
        if owner is None:
            return
        setattr(owner, self._cause_key, label)
        new_val = self._user_getter(owner, self)
        super(ExtendedAliasProperty, self).trigger_change(owner, new_val)

    @staticmethod
    def _weak_ref(obj: Any) -> Any:
        """Вернуть weakref.ref(obj) или WeakProxy как есть; если нельзя ослабить — вернуть объект."""
        if isinstance(obj, WeakProxy):
            return obj
        try:
            return weakref.ref(obj)
        except TypeError:
            return obj

    @staticmethod
    def _deref(ref_or_obj: Any) -> Any | None:
        """Разыменовать weakref/WeakProxy/объект в живой объект; вернуть None, если он уничтожен."""
        try:
            return ref_or_obj() if callable(ref_or_obj) else ref_or_obj
        except ReferenceError:
            return None

    @staticmethod
    def _unbind_by_uid(dispatcher: EventDispatcher, name: str, uid: int) -> None:
        """Снять подписку по uid (совместимо с разными версиями Kivy)."""
        if hasattr(dispatcher, "funbind_uid"):
            dispatcher.funbind_uid(name, uid)
        elif hasattr(dispatcher, "unbind_uid"):
            dispatcher.unbind_uid(name, uid)

    # ---------- Доступ к внутренним структурам (ленивое создание) ----------

    def _get_uid_list(self, obj: EventDispatcher) -> list[tuple[Any, str, int]]:
        uids = getattr(obj, self._uids_key, None)
        if uids is None:
            uids = []
            setattr(obj, self._uids_key, uids)
        return uids

    def _get_chains_map(
        self, obj: EventDispatcher
    ) -> dict[str, list[tuple[Any, str, int]]]:
        chains = getattr(obj, self._chains_key, None)
        if chains is None:
            chains = {}
            setattr(obj, self._chains_key, chains)
        return chains

    def _get_signatures_map(self, obj: EventDispatcher) -> dict[str, tuple[int, ...]]:
        sigs = getattr(obj, self._sig_key, None)
        if sigs is None:
            sigs = {}
            setattr(obj, self._sig_key, sigs)
        return sigs
