import uuid

import jwt
from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer
from pydantic import BaseModel, ValidationError

import apps.business.models


class BusinessToken(BaseModel):
    business_id: uuid.UUID
    token_version: int


class BusinessAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> str | None:
        try:
            decoded_payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            token_payload = BusinessToken(**decoded_payload)
        except (jwt.PyJWTError, ValidationError):
            return None

        try:
            business = apps.business.models.Business.objects.get(
                id=token_payload.business_id
            )
        except apps.business.models.Business.DoesNotExist:
            return None

        if business.token_version != token_payload.token_version:
            return None

        return business
