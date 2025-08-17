from kivy.base import ExceptionHandler, ExceptionManager
from kivy.properties import Logger


class ClockHandler(ExceptionHandler):
    def handle_exception(self, inst):
        if isinstance(inst, ValueError):
            Logger.exception('ValueError caught by ClockHandler')
            return ExceptionManager.PASS
        return ExceptionManager.RAISE
