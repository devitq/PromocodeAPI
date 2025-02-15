from datetime import datetime

import pytz
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django_countries.fields import CountryField

from apps.business.models import Business
from apps.core.models import BaseModel
from apps.promo.validators import (
    PromocodeDurationValidator,
    PromocodeUniqueValidator,
    TargetAgeValidator,
    TargetCategoriesValidator,
)
from apps.user.models import User


class PromocodeTarget(BaseModel):
    age_from = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    age_until = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    country = CountryField(blank=True, null=True)
    country_raw = models.CharField(max_length=2, blank=True, null=True)
    categories = models.JSONField(
        blank=True,
        null=True,
        default=list,
        validators=[TargetCategoriesValidator()],
    )

    def __str__(self) -> str:
        return str(self.id)

    def clean(self) -> None:
        super().clean()

        TargetAgeValidator()(self)


class Promocode(BaseModel):
    class ModeChoices(models.TextChoices):
        COMMON = "COMMON"
        UNIQUE = "UNIQUE"

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="promocodes",
    )
    description = models.TextField(
        max_length=300,
        validators=[MinLengthValidator(10)],
    )
    image_url = models.URLField(
        max_length=350,
        blank=True,
        null=True,
    )
    target = models.ForeignKey(
        PromocodeTarget,
        on_delete=models.CASCADE,
        related_name="promocodes",
    )
    max_count = models.PositiveIntegerField(
        validators=[MaxValueValidator(100000000)],
    )
    active_from = models.DateField(blank=True, null=True)
    active_until = models.DateField(blank=True, null=True)
    mode = models.CharField(max_length=6, choices=ModeChoices)
    promo_common = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        validators=[MinLengthValidator(5)],
    )
    promo_unique = models.JSONField(
        blank=True,
        null=True,
        default=list,
        validators=[PromocodeUniqueValidator()],
    )
    promo_unique_activated = models.JSONField(
        blank=True,
        null=True,
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)

    def clean(self) -> None:
        super().clean()

        if self.image_url == "":
            err = {
                "image_url": "Field cannot be blank.",
            }
            raise ValidationError(err)

        if self.mode == self.ModeChoices.COMMON:
            if not self.promo_common:
                err = {
                    "promo_common": "Field is required for COMMON mode.",
                }
                raise ValidationError(err)
            if self.promo_unique:
                err = {
                    "promo_unique": "Field must be empty for COMMON mode.",
                }
                raise ValidationError(err)
            if self.max_count < self.activations.count():
                err = {
                    "max_count": "Activations count is bigger than max_count",
                }
                raise ValidationError(err)
        elif self.mode == self.ModeChoices.UNIQUE:
            if not self.promo_unique:
                err = {
                    "promo_unique": "Field is required for UNIQUE mode.",
                }
                raise ValidationError(err)
            if self.promo_common:
                err = {
                    "promo_common": "Field must be empty for UNIQUE mode.",
                }
                raise ValidationError(err)
            if self.max_count != 1:
                err = {
                    "max_count": "Field must be 1 for UNIQUE mode.",
                }
                raise ValidationError(err)

        PromocodeDurationValidator()(self)

    def activate_promocode(self, user: User) -> str:
        promocode: str | None = None

        if self.mode == self.ModeChoices.COMMON:
            promocode = self.promo_common
        elif self.mode == self.ModeChoices.UNIQUE:
            unused_promocodes = self.promo_unique[
                len(self.promo_unique_activated) : :
            ]
            promocode = unused_promocodes[0]
            self.promo_unique_activated.append(promocode)
            self.save()

        PromocodeActivation.objects.create(promocode=self, user=user)

        return promocode

    @property
    def active(self) -> bool:
        timezone_utc3 = pytz.timezone("Europe/Moscow")
        current_date = datetime.now(timezone_utc3).date()

        is_active_by_date = (
            self.active_from is None or self.active_from <= current_date
        ) and (self.active_until is None or self.active_until >= current_date)

        if self.mode == self.ModeChoices.COMMON:
            is_active_by_mode = self.activations.count() < self.max_count
        elif self.mode == self.ModeChoices.UNIQUE:
            is_active_by_mode = len(self.promo_unique) > len(
                self.promo_unique_activated
                if self.promo_unique_activated
                else []
            )

        return is_active_by_date and is_active_by_mode


class PromocodeActivation(BaseModel):
    promocode = models.ForeignKey(
        Promocode,
        on_delete=models.CASCADE,
        related_name="activations",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activations",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.promocode.id} | {self.user.id}"


class PromocodeComment(BaseModel):
    promocode = models.ForeignKey(
        Promocode,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(
        max_length=1000,
        validators=[MinLengthValidator(10)],
    )
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.promocode.id} | {self.author.id}"


class PromocodeLike(BaseModel):
    promocode = models.ForeignKey(
        Promocode, on_delete=models.CASCADE, related_name="likes"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="liked_promocodes"
    )

    def __str__(self) -> str:
        return f"{self.promocode.id} | {self.user.id}"

    class Meta:
        unique_together = ("promocode", "user")
