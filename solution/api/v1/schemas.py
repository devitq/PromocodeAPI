from http import HTTPStatus as status
from typing import Any

from ninja import Schema


class UnauthorizedError(Schema):
    detail: str = status.UNAUTHORIZED.phrase


class NotFoundError(Schema):
    detail: str = status.NOT_FOUND.phrase


class BadRequestError(Schema):
    detail: Any


class UniqueConstraintError(Schema):
    detail: Any
