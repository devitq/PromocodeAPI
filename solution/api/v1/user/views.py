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
from config.errors import UniqueConstraintError

router = Router(tags=["user"])


@router.post(
    "/auth/sign-up",
    response={
        status.OK: schemas.UserSignUpOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
        status.CONFLICT: global_schemas.UniqueConstraintError,
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
        like_count=Count("likes"),
        comment_count=Count("comments"),
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

    if filters.category:
        category_lower = filters.category.lower()
        promocodes = promocodes.filter(
            Q(target__categories__icontains=category_lower)
        )

    promocodes = promocodes.all()

    if filters.active is not None:
        promocodes = [p for p in promocodes if p.active == filters.active]

    response["X-Total-Count"] = len(promocodes)

    promocodes = promocodes[filters.offset : filters.offset + filters.limit]

    return status.OK, [
        utils.map_promocode_to_schema(promocode) for promocode in promocodes
    ]


@router.get(
    "/promo/{promocode_id}",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeViewOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
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
            like_count=Count("likes"),
            comment_count=Count("comments"),
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
    },
    exclude_none=True,
)
def add_like(
    request: HttpRequest, promocode_id: str
) -> tuple[status.OK, schemas.PromocodeViewOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    with contextlib.suppress(UniqueConstraintError):
        PromocodeLike.objects.create(promocode=promocodes.first(), user=user)

    return status.OK, schemas.PromocodeLikeOut()


@router.delete(
    "/promo/{promocode_id}/like",
    auth=UserAuth(),
    response={
        status.OK: schemas.PromocodeRemoveLikeOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
    },
    exclude_none=True,
)
def delete_like(
    request: HttpRequest, promocode_id: str
) -> tuple[status.OK, schemas.PromocodeViewOut]:
    user: User = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    with contextlib.suppress(PromocodeLike.DoesNotExist):
        PromocodeLike.objects.get(
            promocode=promocodes.first(), user=user
        ).delete()

    return status.OK, schemas.PromocodeLikeOut()


@router.post(
    "/promo/{promocode_id}/comments",
    auth=UserAuth(),
    response={
        status.CREATED: schemas.CommentOut,
        status.BAD_REQUEST: global_schemas.BadRequestError,
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
    },
    exclude_none=True,
)
def list_comments(
    request: HttpRequest,
    filters: Query[schemas.PromocodeCommentsFilters],
    promocode_id: str,
    response: HttpResponse
) -> tuple[int, schemas.CommentOut]:
    promocodes = Promocode.objects.filter(id=promocode_id)

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.prefetch_related("comments", "comments__author")

    comments = promocodes.first().comments.all()

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
        status.NOT_FOUND: global_schemas.NotFoundError,
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
        status.NOT_FOUND: global_schemas.NotFoundError,
    },
)
def delete_comment(
    request: HttpRequest,
    promocode_id: str,
    comment_id: str,
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

    comment_obj.delete()

    return status.OK, schemas.CommentDeletedOut()
