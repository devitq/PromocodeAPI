import uuid

from django.core.exceptions import ValidationError
from django.db import models

from config.errors import UniqueConstraintError


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        self.full_clean(validate_unique=False)

        try:
            self.validate_unique()
        except ValidationError as e:
            raise UniqueConstraintError(e) from None

        super().save(*args, **kwargs)
