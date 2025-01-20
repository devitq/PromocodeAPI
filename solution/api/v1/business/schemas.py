import re
import uuid
from typing import ClassVar

from ninja import ModelSchema, Schema
from pydantic import EmailStr, field_validator

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


class BusinessSignInIn(Schema):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value: str) -> str:  # noqa: N805
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,60}$"  # noqa: E501
        if not re.match(pattern, value):
            e = (
                "Password must contain at least 8 characters, one uppercase "
                "letter, one lowercase letter, one number, and one special "
                "character (@$!%*?&)."
            )
            raise ValueError(e)
        return value


class BusinessSignInOut(Schema):
    token: str


__all__ = [
    "BusinessSignInIn",
    "BusinessSignInOut",
    "BusinessSignUpIn",
    "BusinessSignUpOut",
]
