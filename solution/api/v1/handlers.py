import logging
from http import HTTPStatus as status

import django.core.exceptions
import django.http
import ninja.errors
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI

from config.errors import UniqueConstraintError

logger = logging.getLogger("django")


def handle_unique_constraint_error(
    request: HttpRequest,
    exc: UniqueConstraintError,
    router: NinjaAPI,
) -> HttpResponse:
    detail = list(exc.validation_error)

    if hasattr(exc, "error_dict"):
        detail = dict(exc.validation_error)

    return router.create_response(
        request,
        {"detail": detail},
        status=status.CONFLICT,
    )


def handle_django_validation_error(
    request: HttpRequest,
    exc: django.core.exceptions.ValidationError,
    router: NinjaAPI,
) -> HttpResponse:
    detail = list(exc)

    if hasattr(exc, "error_dict"):
        detail = dict(exc)

    return router.create_response(
        request,
        {"detail": detail},
        status=status.BAD_REQUEST,
    )


def handle_authentication_error(
    request: HttpRequest,
    exc: ninja.errors.AuthenticationError,
    router: NinjaAPI,
) -> HttpResponse:
    return router.create_response(
        request,
        {"detail": status.UNAUTHORIZED.phrase},
        status=status.UNAUTHORIZED,
    )


def handle_validation_error(
    request: HttpRequest,
    exc: ninja.errors.ValidationError,
    router: NinjaAPI,
) -> HttpResponse:
    return router.create_response(
        request,
        {"detail": exc.errors},
        status=status.BAD_REQUEST,
    )


def handle_not_found_error(
    request: HttpRequest,
    exc: Exception,
    router: NinjaAPI,
) -> HttpResponse:
    return router.create_response(
        request,
        {"detail": status.NOT_FOUND.phrase},
        status=status.NOT_FOUND,
    )


def handle_unknown_exception(
    request: HttpRequest,
    exc: Exception,
    router: NinjaAPI,
) -> HttpResponse:
    logger.exception(exc)

    return router.create_response(
        request,
        {"detail": status.INTERNAL_SERVER_ERROR.phrase},
        status=status.INTERNAL_SERVER_ERROR,
    )


exception_handlers = [
    (UniqueConstraintError, handle_unique_constraint_error),
    (django.core.exceptions.ValidationError, handle_django_validation_error),
    (ninja.errors.AuthenticationError, handle_authentication_error),
    (ninja.errors.ValidationError, handle_validation_error),
    (django.http.Http404, handle_not_found_error),
    (Exception, handle_unknown_exception),
]
