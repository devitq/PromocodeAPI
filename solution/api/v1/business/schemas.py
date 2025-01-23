import datetime
import uuid
from typing import ClassVar, Literal

from ninja import ModelSchema, Schema
from pydantic import Field
from pydantic_extra_types.country import CountryAlpha2

from apps.business.models import Business
from apps.promo.models import Promocode, PromocodeTarget


class BusinessSignUpIn(ModelSchema):
    class Meta:
        model = Business
        fields: ClassVar[list[str]] = [
            Business.name.field.name,
            Business.email.field.name,
            Business.password.field.name,
        ]


class BusinessSignUpOut(Schema):
    token: str
    company_id: uuid.UUID


class BusinessSignInIn(ModelSchema):
    class Meta:
        model = Business
        fields: ClassVar[list[str]] = [
            Business.email.field.name,
            Business.password.field.name,
        ]


class BusinessSignInOut(Schema):
    token: str


class PromocodeTarget(ModelSchema):
    categories: list[str] | None = None
    country: str | None = None

    class Meta:
        model = PromocodeTarget
        fields: ClassVar[list[str]] = [
            PromocodeTarget.age_from.field.name,
            PromocodeTarget.age_until.field.name,
            PromocodeTarget.categories.field.name,
        ]


class CreatePromocodeIn(ModelSchema):
    target: PromocodeTarget
    promo_unique: list[str] | None = None

    class Meta:
        model = Promocode
        fields: ClassVar[list[str]] = [
            Promocode.description.field.name,
            Promocode.image_url.field.name,
            Promocode.max_count.field.name,
            Promocode.active_from.field.name,
            Promocode.active_until.field.name,
            Promocode.mode.field.name,
            Promocode.promo_common.field.name,
        ]


class CreatePromocodeOut(Schema):
    id: uuid.UUID


class PromocodeListFilters(Schema):
    limit: int = Field(10, gt=0, description="Limit must be greater than 0")
    offset: int = Field(
        0, ge=0, description="Offset must be greater than or equal to 0"
    )
    sort_by: Literal["active_from", "active_until", None] = None
    country__in: list[CountryAlpha2] = Field(None, alias="country")


class PromocodeTargetViewOut(Schema):
    age_from: int | None
    age_until: int | None
    country: str | None
    categories: list[str] | None


class PromocodeViewOut(Schema):
    promo_id: uuid.UUID
    company_id: uuid.UUID
    description: str
    image_url: str | None
    target: PromocodeTargetViewOut
    max_count: int
    active_from: datetime.date | None
    active_until: datetime.date | None
    mode: str
    promo_common: str | None
    promo_unique: list[str] | None
    company_name: str
    like_count: int
    used_count: int
    active: bool


class PatchPromocodeIn(Schema):
    description: str | None = None
    image_url: str | None = None
    target: PromocodeTarget | None = None
    max_count: int | None = None
    active_from: datetime.date | None = None
    active_until: datetime.date | None = None


class PromocodeStatsForCountry(Schema):
    country: str
    activations_count: int


class PromocodeStats(Schema):
    activations_count: int
    countries: list[PromocodeStatsForCountry] | None = None
