import uuid
from typing import ClassVar

from ninja import ModelSchema, Schema
from pydantic import Field, StrictInt

from apps.user.models import User


class UserTarget(ModelSchema):
    age: StrictInt

    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            User.country.field.name,
        ]


class UserSignUpIn(ModelSchema):
    other: UserTarget

    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            User.name.field.name,
            User.surname.field.name,
            User.email.field.name,
            User.avatar_url.field.name,
            User.password.field.name,
        ]


class UserSignUpOut(Schema):
    token: str


class UserSignInIn(ModelSchema):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            User.email.field.name,
            User.password.field.name,
        ]


class UserSignInOut(Schema):
    token: str


class ViewUserOut(ModelSchema):
    other: UserTarget

    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            User.name.field.name,
            User.surname.field.name,
            User.email.field.name,
            User.avatar_url.field.name,
        ]


class PatchUserIn(Schema):
    name: str | None = None
    surname: str | None = None
    avatar_url: str | None = None
    password: str | None = None


class PromocodeFeedFilters(Schema):
    limit: int = Field(10, gt=0, description="Limit must be greater than 0")
    offset: int = Field(
        0, ge=0, description="Offset must be greater than or equal to 0"
    )
    category: str | None = None
    active: bool | None = None


class PromocodeViewOut(Schema):
    promo_id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    description: str
    image_url: str | None
    active: bool
    is_activated_by_user: bool
    is_liked_by_user: bool
    like_count: int
    comment_count: int


class PromocodeLikeOut(Schema):
    status: str = "ok"


class PromocodeRemoveLikeOut(Schema):
    status: str = "ok"
