import contextlib
from http import HTTPStatus as status

from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpRequest, HttpResponse
from ninja import Query, Router
from ninja.errors import AuthenticationError, HttpError

from api.v1 import schemas as global_schemas
from api.v1.auth import UserAuth
from api.v1.user import schemas, utils
from apps.promo.models import (
    Promocode,
    PromocodeActivation,
    PromocodeComment,
    PromocodeLike,
)
from apps.user.models import User
from config.errors import ConflictError
from config.integrations.antifraud.interactor import AntifraudServiceInteractor

router = Router(tags=["user"])


@router.post(
    "/auth/sign-up",
    response={
        status.OK: schemas.UserSignUpOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.CONFLICT: global_schemas.ConflictError,
    },
)
def signup(
    request: HttpRequest,
    user: schemas.UserSignUpIn,
) -> tuple[int, schemas.UserSignUpOut]:
    user_obj = User(
        **user.dict(exclude={"other"}),
        **user.other.dict(),
        country_raw=user.other.dict()["country"],
    )
    user_obj.save()

    return status.OK, schemas.UserSignUpOut(
        token=user_obj.generate_token(),
    )


@router.post(
    "/auth/sign-in",
    response={
        status.OK: schemas.UserSignInOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def signin(
    request: HttpRequest,
    login_data: schemas.UserSignInIn,
) -> tuple[int, schemas.UserSignInOut]:
    user_obj = User(**dict(login_data))
    user_obj.validate(
        include=[User.email.field, User.password.field],
        validate_unique=False,
        validate_constraints=False,
    )

    try:
        user_obj = User.objects.get(email=login_data.email)
    except User.DoesNotExist:
        raise AuthenticationError from None

    if user_obj.password != login_data.password:
        raise AuthenticationError

    user_obj.token_version += 1
    user_obj.save()

    return status.OK, schemas.UserSignInOut(
        token=user_obj.generate_token(),
    )


@router.get(
    "/profile",
    auth=UserAuth(),
    response={
        status.OK: schemas.ViewUserOut,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def get_profile(request: HttpRequest) -> tuple[int, schemas.ViewUserOut]:
    user = request.auth

    return status.OK, utils.map_user_to_schema(user)


@router.patch(
    "/profile",
    auth=UserAuth(),
    response={
        status.OK: schemas.ViewUserOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def patch_profile(
    request: HttpRequest, patched_fields: schemas.PatchUserIn
) -> tuple[int, schemas.ViewUserOut]:
    user = request.auth

    patch_data = patched_fields.dict(exclude_unset=True)
    for field, value in patch_data.items():
        setattr(user, field, value)

    user.save()

    return status.OK, utils.map_user_to_schema(user)


@router.get(
    "/feed",
    auth=UserAuth(),
    response={
        status.OK: list[schemas.PromocodeViewOut],
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def feed(
    request: HttpRequest,
    filters: Query[schemas.PromocodeFeedFilters],
    response: HttpResponse,
) -> tuple[status.OK, list[schemas.PromocodeViewOut]]:
    user: User = request.auth

    promocodes = Promocode.objects.select_related("target")

    promocodes = promocodes.filter(
        Q(
            Q(target__age_from__isnull=True)
            | Q(target__age_from__lte=user.age),
            Q(target__age_until__isnull=True)
            | Q(target__age_until__gte=user.age),
            Q(target__country__isnull=True) | Q(target__country=user.country),
        )
    )

    promocodes = promocodes.prefetch_related("likes", "comments").annotate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", distinct=True),
        is_liked_by_user=Exists(
            PromocodeLike.objects.filter(promocode=OuterRef("pk"), user=user)
        ),
        is_activated_by_user=Exists(
            PromocodeActivation.objects.filter(
                promocode=OuterRef("pk"), user=user
            )
        ),
    )

    promocodes = promocodes.order_by("-created_at")

    promocodes = promocodes.all()

    if filters.category:
        category_lower = filters.category.lower()

        def matches_category(promocode: Promocode) -> bool:
            categories = promocode.target.categories or []
            return any(
                category.lower() == category_lower for category in categories
            )

        promocodes = [p for p in promocodes if matches_category(p)]

    if filters.active is not None:
        promocodes = [p for p in promocodes if p.active == filters.active]

    response["X-Total-Count"] = len(promocodes)

    promocodes = promocodes[filters.offset : filters.offset + filters.limit]

    return status.OK, [
        utils.map_promocode_to_schema(promocode) for promocode in promocodes
    ]


@router.get(
    "/promo/history",
    auth=UserAuth(),
    response={
        status.OK: list[schemas.PromocodeViewOut],
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def get_activations_history(
    request: HttpRequest,
    filters: Query[schemas.ActivationsHistoryFilters],
    response: HttpResponse,
) -> tuple[int, list[schemas.PromocodeViewOut]]:
    user: User = request.auth

    activations = (
        PromocodeActivation.objects.filter(user=user)
        .select_related("promocode", "promocode__business")
        .prefetch_related("promocode__likes", "promocode__comments")
        .annotate(
            like_count=Count("promocode__likes", distinct=True),
            comment_count=Count("promocode__comments", distinct=True),
            is_liked_by_user=Exists(
                PromocodeLike.objects.filter(
                    promocode=OuterRef("promocode"), user=user
                )
            ),
        )
        .order_by("-timestamp")
    )

    promocodes = []
    for activation in activations:
        promocode = activation.promocode
        promocode.like_count = activation.like_count
        promocode.comment_count = activation.comment_count
        promocode.is_liked_by_user = activation.is_liked_by_user
        promocode.is_activated_by_user = True
        promocodes.append(utils.map_promocode_to_schema(promocode))

    response["X-Total-Count"] = len(promocodes)

    promocodes = promocodes[filters.offset : filters.offset + filters.limit]

    return status.OK, promocodes


@router.get(
    "/promo/{promocode_id}",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeViewOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def get_promocode(
    request: HttpRequest, promocode_id: str
) -> tuple[status.OK, schemas.PromocodeViewOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = (
        promocodes.select_related("business")
        .prefetch_related("likes", "comments")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
            is_liked_by_user=Exists(
                PromocodeLike.objects.filter(
                    promocode=OuterRef("pk"), user=user
                )
            ),
            is_activated_by_user=Exists(
                PromocodeActivation.objects.filter(
                    promocode=OuterRef("pk"), user=user
                )
            ),
        )
    )

    promocode = promocodes.first()

    return status.OK, utils.map_promocode_to_schema(promocode)


@router.post(
    "/promo/{promocode_id}/like",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeLikeOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def add_like(
    request: HttpRequest, promocode_id: str
) -> tuple[status.OK, schemas.PromocodeLikeOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    with contextlib.suppress(ConflictError):
        PromocodeLike.objects.create(promocode=promocodes.first(), user=user)

    return status.OK, schemas.PromocodeLikeOut()


@router.delete(
    "/promo/{promocode_id}/like",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeRemoveLikeOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def delete_like(
    request: HttpRequest, promocode_id: str
) -> tuple[status.OK, schemas.PromocodeRemoveLikeOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    with contextlib.suppress(PromocodeLike.DoesNotExist):
        PromocodeLike.objects.get(
            promocode=promocodes.first(), user=user
        ).delete()

    return status.OK, schemas.PromocodeRemoveLikeOut()


@router.post(
    "/promo/{promocode_id}/comments",
    auth=UserAuth(),
    response={
        status.CREATED: schemas.CommentOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def add_comment(
    request: HttpRequest, promocode_id: str, comment: schemas.CommentIn
) -> tuple[int, schemas.CommentOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    comment_obj = PromocodeComment(
        promocode=promocodes.first(), author=user, **comment.dict()
    )
    comment_obj.save()

    return status.CREATED, utils.map_comment_to_schema(comment_obj)


@router.get(
    "/promo/{promocode_id}/comments",
    auth=UserAuth(),
    response={
        status.OK: list[schemas.CommentOut],
        status.NOT_FOUND: global_schemas.NotFoundError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def list_comments(
    request: HttpRequest,
    filters: Query[schemas.PromocodeCommentsFilters],
    promocode_id: str,
    response: HttpResponse,
) -> tuple[int, list[schemas.CommentOut]]:
    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.prefetch_related("comments", "comments__author")

    comments = promocodes.first().comments.order_by("-date").all()

    response["X-Total-Count"] = len(comments)

    comments = comments[filters.offset : filters.offset + filters.limit]

    return status.OK, [
        utils.map_comment_to_schema(comment) for comment in comments
    ]


@router.get(
    "/promo/{promocode_id}/comments/{comment_id}",
    auth=UserAuth(),
    response={
        status.OK: schemas.CommentOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def get_comment(
    request: HttpRequest, promocode_id: str, comment_id: str
) -> tuple[int, schemas.CommentOut]:
    commnets = PromocodeComment.objects.filter(
        id=comment_id, promocode_id=promocode_id
    )

    if not commnets.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    comment = commnets.select_related("author").first()

    return status.OK, utils.map_comment_to_schema(comment)


@router.put(
    "/promo/{promocode_id}/comments/{comment_id}",
    auth=UserAuth(),
    response={
        status.OK: schemas.CommentOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
    exclude_none=True,
)
def update_comment(
    request: HttpRequest,
    promocode_id: str,
    comment_id: str,
    comment: schemas.CommentIn,
) -> tuple[int, schemas.CommentOut]:
    user: User = request.auth

    commnets = PromocodeComment.objects.filter(
        id=comment_id, promocode_id=promocode_id
    )

    if not commnets.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    comments = commnets.select_related("author").filter(author=user)

    if not comments.exists():
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    comment_obj = comments.first()

    put_data = comment.dict()
    for field, value in put_data.items():
        setattr(comment_obj, field, value)

    comment_obj.save()

    return status.OK, utils.map_comment_to_schema(comment_obj)


@router.delete(
    "/promo/{promocode_id}/comments/{comment_id}",
    auth=UserAuth(),
    response={
        status.OK: schemas.CommentDeletedOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def delete_comment(
    request: HttpRequest,
    promocode_id: str,
    comment_id: str,
) -> tuple[int, schemas.CommentDeletedOut]:
    user: User = request.auth

    commnets = PromocodeComment.objects.filter(
        id=comment_id, promocode_id=promocode_id
    )

    if not commnets.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    comments = commnets.select_related("author").filter(author=user)

    if not comments.exists():
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    comment_obj = comments.first()

    comment_obj.delete()

    return status.OK, schemas.CommentDeletedOut()


@router.post(
    "/promo/{promocode_id}/activate",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeActivateOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def activate_promocode(
    request: HttpRequest,
    promocode_id: str,
) -> tuple[int, schemas.PromocodeActivateOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.select_related("target").filter(
        Q(
            Q(target__age_from__isnull=True)
            | Q(target__age_from__lte=user.age),
            Q(target__age_until__isnull=True)
            | Q(target__age_until__gte=user.age),
            Q(target__country__isnull=True) | Q(target__country=user.country),
        )
    )

    if not promocodes.exists():
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    promocode = promocodes.first()

    if not promocode.active:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    antifraud_result = AntifraudServiceInteractor().validate(
        user_email=user.email, promo_id=str(promocode.id)
    )

    if not antifraud_result["ok"]:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    promo = promocode.activate_promocode(user)

    return status.OK, schemas.PromocodeActivateOut(promo=promo)
