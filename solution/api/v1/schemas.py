from http import HTTPStatus as status

from ninja import Schema


class UnauthorizedError(Schema):
    detail: str = status.UNAUTHORIZED.phrase


class NotFoundError(Schema):
    detail: str = status.NOT_FOUND.phrase


class ValidationError(Schema):
    detail: str


class UniqueConstraintError(Schema):
    detail: str
