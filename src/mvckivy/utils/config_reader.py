import os
from kivy import platform


class ConfigReader:
    _debug_mode: bool | None = None

    @classmethod
    def get_debug_mode(cls) -> bool:
        if cls._debug_mode is not None:
            return cls._debug_mode

        if platform == "android":
            cls._debug_mode = cls.__read_from_application_info()
        else:
            cls._debug_mode = cls.__read_from_env()

        return cls._debug_mode

    @staticmethod
    def __read_from_env() -> bool:
        return os.environ.get("MVCKIVY_DEBUG_MODE", "False").lower() in [
            "true",
            "1",
            "yes",
        ]

    @staticmethod
    def __read_from_application_info() -> bool:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        ApplicationInfo = autoclass("android.content.pm.ApplicationInfo")
        info = activity.getApplicationInfo()
        return (info.flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0
