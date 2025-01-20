import jwt
from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

from apps.core.models import BaseModel


class Business(BaseModel):
    name = models.CharField(max_length=50, validators=[MinLengthValidator(5)])
    email = models.EmailField(
        unique=True,
        max_length=120,
        validators=[MinLengthValidator(8)],
    )
    password = models.CharField(
        max_length=60,
        validators=[
            RegexValidator(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
            ),
        ],
    )
    token_version = models.BigIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    def generate_token(self) -> str:
        return jwt.encode(
            {
                "business_id": str(self.id),
                "token_version": self.token_version,
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
