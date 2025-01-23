from django.core.exceptions import ValidationError


class UniqueConstraintError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.validation_error = validation_error
