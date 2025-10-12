from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from i18n import set_locale

class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # قبل از اینکه request وارد route بشه، زبان رو ست کن
        await set_locale(request)
        response = await call_next(request)
        return response
