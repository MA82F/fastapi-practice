import gettext
from pathlib import Path


class TranslationWrapper:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_translation()
        return cls._instance

    def init_translation(self):
        lang = "en"  # زبان پیش‌فرض
        locales_dir = Path(__file__).parent / "translations"
        self.translations = gettext.translation(
            "messages", localedir=locales_dir, languages=[lang], fallback=True
        )
        self.translations.install()

    def gettext(self, message: str) -> str:
        return self.translations.gettext(message)


def _(message: str) -> str:
    wrapper = TranslationWrapper()
    return wrapper.gettext(message)


async def set_locale(request):
    wrapper = TranslationWrapper()
    lang_header = request.headers.get("accept-language", "en")
    # ممکنه header شامل چند زبان باشه؛ برای سادگی فقط زبان اول رو جدا می‌کنیم
    lang_code = lang_header.split(",")[0].lower()
    locales_dir = Path(__file__).parent / "translations"
    wrapper.translations = gettext.translation(
        "messages", localedir=locales_dir, languages=[lang_code], fallback=True
    )
    wrapper.translations.install()
