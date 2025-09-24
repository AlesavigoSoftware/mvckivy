from mvckivy import logger
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.transition.transition import MDTransitionBase


class MKVScreenManager(MDScreenManager):
    def check_transition(self, *args) -> None:
        if not issubclass(self.transition.__class__, MDTransitionBase):
            logger.warning(
                f"Registered transition {self.transition.__class__} is not compatible with Hero transition"
            )
