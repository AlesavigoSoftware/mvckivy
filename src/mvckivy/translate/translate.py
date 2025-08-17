import gettext


class Trans:
    """
    Generic python translations, no KV support, just PY.

    Should handle tracking language in "Trans.lang"
    """

    lang = "en"

    @classmethod
    def get_current_language(cls):
        return cls.lang

    @classmethod
    def switch_language(cls, language):
        print("setting language:", language)

        lang = gettext.translation("kivyapp", localedir="locale", languages=[language])
        lang.install()

        cls.lang = language
        cls._ = lang.gettext

    @classmethod
    def refresh_translations(cls):
        # not needed I think
        pass

