import weakref


class InstanceTrackerMixin:
    instances = weakref.WeakSet()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        InstanceTrackerMixin.instances.add(self)
