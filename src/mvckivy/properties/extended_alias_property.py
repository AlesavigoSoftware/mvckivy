from __future__ import annotations

from functools import partial
from typing import Any, Dict, List, Sequence, Tuple
import weakref

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty
from kivy.weakproxy import WeakProxy


def _weakify(obj: Any):
    """
    Возвращает weakref.ref(obj), если возможно.
    Если obj — WeakProxy или не weakref-able — возвращает сам obj (это безопасно).
    """
    if isinstance(obj, WeakProxy):
        return obj
    try:
        return weakref.ref(obj)
    except TypeError:
        # Невозможно обернуть в weakref (редкий случай) — как fallback вернём сам объект.
        # В Kivy это обычно WeakProxy; для произвольных типов лучше избегать сильной ссылки,
        # но в рамках EventDispatcher практически все типы weakref-able.
        return obj


def _deref(ref_or_obj: Any):
    """
    Приводит хранимую сущность к «живому» объекту:
      - если это weakref.ref -> ref()
      - иначе -> сам объект (включая WeakProxy)
    """
    try:
        return ref_or_obj() if callable(ref_or_obj) else ref_or_obj
    except ReferenceError:
        return None


def _funbind_uid(dispatcher: EventDispatcher, name: str, uid: int) -> None:
    """
    Безопасно снимает бинды по uid для разных версий/сборок Kivy.
    """
    if hasattr(dispatcher, "funbind_uid"):
        dispatcher.funbind_uid(name, uid)
    elif hasattr(dispatcher, "unbind_uid"):
        dispatcher.unbind_uid(name, uid)


class ExtendedAliasProperty(AliasProperty):
    """
    AliasProperty с поддержкой:
      • цепочек зависимостей 'a.b.c' (property-of-property),
      • строгого rebind (промежуточные звенья ребиндятся только при rebind=True),
      • отложенного ребилда (через Clock) — нет гонок и лавинообразных перестроений,
      • слабых ссылок/WeakProxy — нет утечек,
      • last_cause() -> 'a' / 'a.b' / 'a.b.c',
      • dispose(obj) — ручной сброс всех слушателей.

    Конструктор:
      getter(obj, ext) -> Any
      setter(obj, value, ext) -> bool|None
      bind: iterable[str]             имена зависимостей; допустимы dotted-пути
      cache, watch_before_use — по смыслу как в AliasProperty
      respect_rebind_flag: True       ребилд цепочки для промежуточных узлов только если у Property rebind=True
    """

    def __init__(
        self,
        getter,
        setter=None,
        *,
        bind: Sequence[str] = (),
        cache: bool = False,
        watch_before_use: bool = True,
        respect_rebind_flag: bool = True,
        **kwargs,
    ):
        self._ext_bind: Tuple[str, ...] = tuple(bind)
        self._getter_ref = getter
        self._respect_rebind_flag = respect_rebind_flag

        sid = id(self)
        # Ключи для хранения состояния на владельце алиаса
        self._linked_key = f"__ap_linked_{sid}"
        self._cause_key = f"__ap_cause_{sid}"
        self._uids_key = f"__ap_uids_{sid}"  # List[(ref_or_obj, name, uid)]
        self._chains_key = f"__ap_chains_{sid}"  # path -> List[(ref_or_obj, name, uid)]
        self._triggers_key = f"__ap_triggers_{sid}"  # path -> ClockEvent
        self._sig_key = f"__ap_sig_{sid}"  # path -> tuple(signature)

        super().__init__(
            lambda obj: getter(obj, self),
            setter,
            bind=(),  # отключаем внутренние bind'ы AliasProperty — всё делаем сами
            cache=cache,
            watch_before_use=watch_before_use,
            **kwargs,
        )

    def last_cause(self, obj):
        return getattr(obj, self._cause_key, None)

    def dispose(self, obj: EventDispatcher) -> None:
        """Снять все слушатели и очистить служебные структуры на владельце алиаса."""
        uids = getattr(obj, self._uids_key, None) or []
        for ref_or_obj, name, uid in uids:
            d = _deref(ref_or_obj)
            if d is not None:
                try:
                    _funbind_uid(d, name, uid)
                except Exception:
                    pass
        setattr(obj, self._uids_key, [])

        chains = getattr(obj, self._chains_key, None) or {}
        for path, bundle in list(chains.items()):
            for ref_or_obj, name, uid in bundle:
                d = _deref(ref_or_obj)
                if d is not None:
                    try:
                        _funbind_uid(d, name, uid)
                    except Exception:
                        pass
        setattr(obj, self._chains_key, {})

        triggers = getattr(obj, self._triggers_key, None) or {}
        for _, ev in list(triggers.items()):
            try:
                ev.cancel()
            except Exception:
                pass
        setattr(obj, self._triggers_key, {})

        setattr(obj, self._sig_key, {})
        setattr(obj, self._linked_key, False)
        setattr(obj, self._cause_key, None)

    def _m_uids(self, obj) -> List[Tuple[Any, str, int]]:
        u = getattr(obj, self._uids_key, None)
        if u is None:
            u = []
            setattr(obj, self._uids_key, u)
        return u

    def _m_chains(self, obj) -> Dict[str, List[Tuple[Any, str, int]]]:
        d = getattr(obj, self._chains_key, None)
        if d is None:
            d = {}
            setattr(obj, self._chains_key, d)
        return d

    def _m_triggers(self, obj) -> Dict[str, Any]:
        d = getattr(obj, self._triggers_key, None)
        if d is None:
            d = {}
            setattr(obj, self._triggers_key, d)
        return d

    def _m_sigs(self, obj) -> Dict[str, Tuple[int, ...]]:
        d = getattr(obj, self._sig_key, None)
        if d is None:
            d = {}
            setattr(obj, self._sig_key, d)
        return d

    def _ensure_linked(self, obj: EventDispatcher) -> None:
        if getattr(obj, self._linked_key, False):
            return

        uids = self._m_uids(obj)
        owner_ref = _weakify(obj)

        def bind_simple(prop_name: str, label: str) -> None:
            cb = partial(self._on_dep, label, owner_ref)
            uid = obj.fbind(prop_name, cb)
            if uid:
                uids.append((_weakify(obj), prop_name, uid))

        for name in self._ext_bind:
            if "." in name:
                self._link_chain(obj, name, defer=False)  # первичная привязка — сразу
            else:
                bind_simple(name, name)

        setattr(obj, self._linked_key, True)

    def _schedule_relink(self, root_obj: EventDispatcher, path: str) -> None:
        triggers = self._m_triggers(root_obj)
        ev = triggers.get(path)
        if ev is None:
            owner_ref = _weakify(root_obj)

            def _do_relink(_dt):
                root = _deref(owner_ref)
                if root is not None:
                    self._link_chain(root, path, defer=False)

            ev = Clock.create_trigger(_do_relink, 0)
            triggers[path] = ev

        ev()  # схлопывает множественные вызовы в один кадр

    def _calc_signature(self, root_obj: EventDispatcher, path: str) -> Tuple[int, ...]:
        segs = path.split(".")
        disp: Any = root_obj
        sig: List[int] = []
        for i, seg in enumerate(segs):
            if not isinstance(disp, EventDispatcher):
                sig.append(0)
                break
            try:
                _ = disp.property(seg, quiet=True)
            except Exception:
                _ = None
            sig.append(id(disp))
            if i < len(segs) - 1:
                try:
                    disp = getattr(disp, seg)
                except Exception:
                    disp = None
        return tuple(sig)

    def _link_chain(self, root_obj: EventDispatcher, path: str, *, defer: bool) -> None:
        if defer:
            self._schedule_relink(root_obj, path)
            return

        # если структура пути не изменилась — не ребиндим снова
        sigs = self._m_sigs(root_obj)
        new_sig = self._calc_signature(root_obj, path)
        if sigs.get(path) == new_sig:
            return
        sigs[path] = new_sig

        # снять старые слушатели
        self._unlink_chain(root_obj, path)

        chains = self._m_chains(root_obj)
        segs = path.split(".")
        disp: Any = root_obj
        watchers: List[Tuple[Any, str, int]] = []
        owner_ref = _weakify(root_obj)

        def _fbind(d: EventDispatcher, prop: str, cb) -> None:
            uid = d.fbind(prop, cb)
            if uid:
                watchers.append((_weakify(d), prop, uid))

        def _should_rebind_strict(d: EventDispatcher, prop: str) -> bool:
            if not self._respect_rebind_flag:
                return True
            try:
                p = d.property(prop, quiet=True)
            except Exception:
                p = None
            if p is None:
                return False
            return bool(getattr(p, "rebind", False))

        for i, seg in enumerate(segs):
            if not isinstance(disp, EventDispatcher):
                break

            is_leaf = i == len(segs) - 1

            if is_leaf:
                cb = partial(self._on_dep, path, owner_ref)
                _fbind(disp, seg, cb)
            else:
                idx = i

                def node_cb(inst, value, _idx=idx, _seg=seg):
                    root = _deref(owner_ref)
                    if root is None:
                        return
                    setattr(root, self._cause_key, ".".join(segs[: _idx + 1]))
                    if _should_rebind_strict(inst, _seg):
                        self._schedule_relink(root, path)
                    new_val = self._getter_ref(root, self)
                    super(ExtendedAliasProperty, self).trigger_change(root, new_val)

                _fbind(disp, seg, node_cb)

                try:
                    disp = getattr(disp, seg)
                except Exception:
                    disp = None

        chains[path] = watchers

    def _unlink_chain(self, root_obj: EventDispatcher, path: str) -> None:
        chains = self._m_chains(root_obj)
        old = chains.pop(path, None)
        if not old:
            return
        for ref_or_obj, name, uid in old:
            d = _deref(ref_or_obj)
            if d is not None:
                try:
                    _funbind_uid(d, name, uid)
                except Exception:
                    pass

    def _on_dep(self, label: str, owner_ref, _inst, _value):
        root = _deref(owner_ref)
        if root is None:
            return
        setattr(root, self._cause_key, label)
        new_val = self._getter_ref(root, self)
        super(ExtendedAliasProperty, self).trigger_change(root, new_val)

    def get(self, obj):
        self._ensure_linked(obj)
        return super().get(obj)

    def set(self, obj, value):
        self._ensure_linked(obj)
        return super().set(obj, value)
