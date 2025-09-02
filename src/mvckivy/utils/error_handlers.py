import logging
import traceback
from typing import TYPE_CHECKING

from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager


if TYPE_CHECKING:
    from mvckivy.app import MVCDebugApp


logger = logging.getLogger("mvckivy")


class ClockHandler(ExceptionHandler):
    def handle_exception(self, inst):
        if isinstance(inst, ValueError):
            logger.exception('ValueError caught by ClockHandler')
            return ExceptionManager.PASS
        return ExceptionManager.RAISE


class AppExceptionNotifyHandler(ExceptionHandler):
    def handle_exception(self, inst):
        if isinstance(inst, (KeyboardInterrupt, SystemExit)):
            return ExceptionManager.RAISE
        app: MVCDebugApp = App.get_running_app()
        if not app.debug_mode and app.raise_error:
            return ExceptionManager.RAISE
        logger.exception(traceback.format_exc())
        app.set_error(inst, tb=traceback.format_exc())
        return ExceptionManager.PASS
