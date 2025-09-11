from functools import partial

from kivy.properties import AliasProperty


class ExtendedAliasProperty(AliasProperty):
    """
    AliasProperty, который сам вешает бинды на зависимости,
    помечает «причину» и триггерит пересчёт.
    """

    def __init__(
        self,
        getter,
        setter=None,
        *,
        bind=(),
        cache=False,
        watch_before_use=True,
        track_components=True,
        **kwargs,
    ):
        # сохраним параметры для собственной схемы биндинга
        self._ext_bind = tuple(bind)  # имена зависимостей (str)
        self._track_components = track_components
        self._getter_ref = getter  # прямой вызов геттера (без .get())
        # ключи для хранения служебного состояния на инстансе
        self._linked_key = f"__ap_linked_{id(self)}"
        self._cause_key = f"__ap_cause_{id(self)}"
        self._uids_key = f"__ap_uids_{id(self)}"

        # важно: отключаем внутренние bind'ы AliasProperty (иначе будет двойная реакция)
        super().__init__(
            lambda obj: getter(obj, self),
            setter,
            bind=(),
            cache=cache,
            watch_before_use=watch_before_use,
            **kwargs,
        )

    # --- публичное API для геттера ---
    def last_cause(self, obj):
        """Вернуть последнюю «причину» вида 'size', 'size.width', 'pos.y', ..."""
        return getattr(obj, self._cause_key, None)

    # --- инфраструктура: ставим собственные бинды при первом использовании ---
    def _ensure_linked(self, obj):
        if getattr(obj, self._linked_key, False):
            return
        uids = []

        def bind_one(prop_name, label):
            # label пишем как хотим видеть в логах (например 'size.width')
            uid = obj.fbind(prop_name, partial(self._on_dep, label))
            uids.append(uid)

        for name in self._ext_bind:
            # биндимся на саму зависимость...
            bind_one(name, name)

            if self._track_components:
                # ...и на её компоненты, если это ReferenceListProperty
                try:
                    p = obj.property(name)
                except Exception:
                    p = None
                comps = getattr(p, "properties", None) or getattr(p, "propnames", None)
                if comps:
                    for comp in comps:
                        bind_one(comp, f"{name}.{comp}")

        setattr(obj, self._uids_key, uids)
        setattr(obj, self._linked_key, True)

    def _on_dep(self, label, inst, value):
        # помечаем «причину»
        setattr(inst, self._cause_key, label)
        # пересчитываем значение через исходный getter и диспатчим одно обновление
        new_val = self._getter_ref(inst, self)
        super().trigger_change(inst, new_val)

    # Важно гарантировать установку биндов при первом чтении/записи свойства
    def get(self, obj):
        self._ensure_linked(obj)
        return super().get(obj)

    def set(self, obj, value):
        self._ensure_linked(obj)
        return super().set(obj, value)
