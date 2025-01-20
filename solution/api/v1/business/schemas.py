import uuid
from typing import ClassVar

from ninja import ModelSchema, Schema
from pydantic import EmailStr

from apps.business.models import Business


class BusinessSignUpIn(ModelSchema):
    email: EmailStr

    class Meta:
        model = Business
        fields: ClassVar[list[str]] = [
            Business.name.field.name,
            Business.password.field.name,
        ]


class BusinessSignUpOut(Schema):
    token: str
    company_id: uuid.UUID


class BusinessSignInIn(ModelSchema):
    email: EmailStr

    class Meta:
        model = Business
        fields: ClassVar[list[str]] = [
            Business.password.field.name,
        ]


class BusinessSignInOut(Schema):
    token: str


__all__ = [
    "BusinessSignInIn",
    "BusinessSignInOut",
    "BusinessSignUpIn",
    "BusinessSignUpOut",
]
