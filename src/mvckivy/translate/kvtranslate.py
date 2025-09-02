import gettext

from kivy.app import App


class TransDict(dict):
    """
    Normal dict, but handle missing strings and replace them by "???????".
    It helps to find strings that are not included in translate dicts.
    """

    def __getitem__(self, key):
        try:
            val = super().__getitem__(key)

        except KeyError:
            val = "???????"

        return val


class Trans:
    """
    Can handle including translations in KV as properties,
    so tey change on "refresh_translations".

    Should handle tracking language in app.settings["lang"]
    """

    lang = None
    kv_translations = {}

    @classmethod
    def get_current_language(cls):
        app = App.get_running_app()
        return app.settings

    @classmethod
    def switch_language(cls, language):
        app = App.get_running_app()

        if app:
            app.settings["lang"] = language

        lang = gettext.translation("kivyapp", localedir="locale", languages=[language])
        lang.install()

        cls._ = lang.gettext

    @classmethod
    def refresh_translations(cls):
        new_dict = TransDict()

        for key in cls.kv_translations.keys():
            new_dict[key] = Trans._(key)

        app = App.get_running_app()
        app.trans = new_dict
