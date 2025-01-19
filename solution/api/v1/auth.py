from django.http import HttpRequest
from ninja.security import HttpBearer


class BearerAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> str | None:
        if token == "will implement later":
            return token

        return None
