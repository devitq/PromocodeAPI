from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible

MAX_CATEGORIES_LIST_LEN = 20
MIN_CATEGORY_LEN = 2
MAX_CATEGORY_LEN = 20

MIN_UNIQUE_PROMOCODES_LIST_LEN = 1
MAX_UNIQUE_PROMOCODES_LIST_LEN = 5000
MIN_UNIQUE_PROMOCODE_LEN = 3
MAX_UNIQUE_PROMOCODE_LEN = 30


class TargetAgeValidator:
    def __call__(self, instance) -> None:  # noqa: ANN001
        if (
            instance.age_from is not None
            and instance.age_until is not None
            and instance.age_from > instance.age_until
        ):
            err = "age_from can't be greater than age_until"
            raise ValidationError(err)


class PromocodeDurationValidator:
    def __call__(self, instance) -> None:  # noqa: ANN001
        if (
            instance.active_from is not None
            and instance.active_until is not None
            and instance.active_from > instance.active_until
        ):
            err = "active_from can't be greater than active_until"
            raise ValidationError(err)


@deconstructible
class TargetCategoriesValidator(BaseValidator):
    def __init__(self) -> None:
        pass

    def __call__(self, categories: list) -> None:
        if not isinstance(categories, list):
            err = "categories must be a list"
            raise ValidationError(err)

        if len(categories) > MAX_CATEGORIES_LIST_LEN:
            err = "max. categories length is 20"
            raise ValidationError(err)

        for category in categories:
            if not (MIN_CATEGORY_LEN <= len(category) <= MAX_CATEGORY_LEN):
                err = "category name length must be >=2 and <=20"
                raise ValidationError(err)


@deconstructible
class PromocodeUniqueValidator(BaseValidator):
    def __init__(self) -> None:
        pass

    def __call__(self, promocodes: list) -> None:
        if not isinstance(promocodes, list):
            err = "unique promocodes must be a list"
            raise ValidationError(err)

        if not (
            MIN_UNIQUE_PROMOCODES_LIST_LEN
            <= len(promocodes)
            <= MAX_UNIQUE_PROMOCODES_LIST_LEN
        ):
            err = "unique promocodes length must be >=1 and <=5000"
            raise ValidationError(err)

        for promocode in promocodes:
            if not (
                MIN_UNIQUE_PROMOCODE_LEN
                <= len(promocode)
                <= MAX_UNIQUE_PROMOCODE_LEN
            ):
                err = "unique promocode length must be >=3 and <=30"
                raise ValidationError(err)
