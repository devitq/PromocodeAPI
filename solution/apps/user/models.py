from datetime import timedelta

import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField

from apps.core.models import BaseModel


class User(BaseModel):
    name = models.CharField(max_length=100, validators=[MinLengthValidator(1)])
    surname = models.CharField(
        max_length=120,
        validators=[MinLengthValidator(1)],
    )
    email = models.EmailField(
        unique=True,
        max_length=120,
        validators=[MinLengthValidator(8)],
    )
    avatar_url = models.URLField(max_length=350, blank=True, null=True)
    age = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    country = CountryField(max_length=2)
    country_raw = models.CharField(max_length=2)
    password = models.CharField(
        max_length=60,
        validators=[
            RegexValidator(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
            ),
        ],
    )
    token_version = models.BigIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.surname} {self.name}"

    def clean(self) -> None:
        super().clean()

        if self.avatar_url == "":
            err = {
                "avatar_url": "Field cannot be blank.",
            }
            raise ValidationError(err)

    def generate_token(self) -> str:
        return jwt.encode(
            {
                "user_id": str(self.id),
                "token_version": self.token_version,
                "exp": timezone.now() + timedelta(hours=24),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
