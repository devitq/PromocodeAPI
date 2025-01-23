import datetime
from collections import Counter
from http import HTTPStatus as status

from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from ninja import Query, Router
from ninja.errors import AuthenticationError, HttpError

from api.v1 import schemas as global_schemas
from api.v1.auth import BusinessAuth
from api.v1.business import schemas, utils
from apps.business.models import Business
from apps.promo.models import Promocode, PromocodeTarget

router = Router(tags=["business"])


@router.post(
    "/auth/sign-up",
    response={
        status.OK: schemas.BusinessSignUpOut,
        status.BAD_REQUEST: global_schemas.ValidationError,
        status.CONFLICT: global_schemas.UniqueConstraintError,
    },
)
def signup(
    request: HttpRequest,
    business: schemas.BusinessSignUpIn,
) -> tuple[int, schemas.BusinessSignUpOut]:
    business_obj = Business(**business.dict())
    business_obj.save()

    return status.OK, schemas.BusinessSignUpOut(
        token=business_obj.generate_token(),
        company_id=business_obj.id,
    )


@router.post(
    "/auth/sign-in",
    response={
        status.OK: schemas.BusinessSignInOut,
        status.BAD_REQUEST: global_schemas.ValidationError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def signin(
    request: HttpRequest,
    login_data: schemas.BusinessSignInIn,
) -> tuple[int, schemas.BusinessSignInOut]:
    business_obj = Business(**dict(login_data))
    business_obj.validate(
        include=[Business.email.field, Business.password.field],
        validate_unique=False,
        validate_constraints=False,
    )

    try:
        business_obj = Business.objects.get(email=login_data.email)
    except Business.DoesNotExist:
        raise AuthenticationError from None

    if business_obj.password != login_data.password:
        raise AuthenticationError

    business_obj.token_version += 1
    business_obj.save()

    return status.OK, schemas.BusinessSignInOut(
        token=business_obj.generate_token(),
    )


@router.post(
    "/promo",
    auth=BusinessAuth(),
    response={
        status.CREATED: schemas.CreatePromocodeOut,
        status.BAD_REQUEST: global_schemas.ValidationError,
        status.UNAUTHORIZED: global_schemas.UnauthorizedError,
    },
)
def create_promocode(
    request: HttpRequest,
    promocode: schemas.CreatePromocodeIn,
) -> schemas.CreatePromocodeOut:
    business = request.auth
    promocode = dict(promocode)
    target = dict(promocode.pop("target"))

    target_obj = PromocodeTarget(**target, country_raw=target["country"])
    target_obj.save()

    promocode_obj = Promocode(
        business=business,
        target=target_obj,
        **promocode,
    )
    try:
        promocode_obj.save()
    except ValidationError as e:
        target_obj.delete()
        raise e  # noqa: TRY201

    return status.CREATED, schemas.CreatePromocodeOut(id=promocode_obj.id)


@router.get(
    "/promo",
    auth=BusinessAuth(),
    response={
        status.OK: list[schemas.PromocodeViewOut],
        status.BAD_REQUEST: global_schemas.ValidationError,
    },
    exclude_none=True,
)
def list_promocode(
    request: HttpRequest,
    filters: Query[schemas.PromocodeListFilters],
    response: HttpResponse,
) -> list[schemas.PromocodeViewOut]:
    business = request.auth

    promocodes = Promocode.objects.filter(business=business).select_related(
        "target", "business"
    )

    if filters.country__in:
        promocodes = promocodes.filter(
            Q(target__country__in=filters.country__in)
            | Q(target__country__isnull=True)
        )

    response["X-Total-Count"] = promocodes.count()

    min_datetime = datetime.date(datetime.MINYEAR, 1, 1)
    max_datetime = datetime.date(datetime.MAXYEAR, 1, 1)

    if filters.sort_by == "active_from":
        promocodes = promocodes.annotate(
            active_from_sort=Coalesce("active_from", Value(min_datetime))
        ).order_by("-active_from_sort")
    elif filters.sort_by == "active_until":
        promocodes = promocodes.annotate(
            active_until_sort=Coalesce("active_until", Value(max_datetime))
        ).order_by("-active_until_sort")
    else:
        promocodes = promocodes.order_by("-created_at")

    promocodes = promocodes.annotate(
        used_count=Count("activations"),
        like_count=Count("likes"),
    )

    promocodes = promocodes[filters.offset : filters.offset + filters.limit]

    return [
        utils.map_promocode_to_schema(promocode) for promocode in promocodes
    ]


@router.get(
    "/promo/{promocode_id}",
    auth=BusinessAuth(),
    response={
        status.OK: schemas.PromocodeViewOut,
        status.NOT_FOUND: global_schemas.NotFoundError,
    },
    exclude_none=True,
)
def get_promocode(
    request: HttpRequest, promocode_id: str
) -> schemas.PromocodeViewOut:
    business = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id).select_related(
        "target", "business"
    )

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.annotate(
        used_count=Count("activations"),
        like_count=Count("likes"),
    )

    promocode = promocodes.first()

    if promocode.business != business:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    return utils.map_promocode_to_schema(promocode)


@router.patch(
    "/promo/{promocode_id}",
    auth=BusinessAuth(),
    response={
        status.OK: schemas.PromocodeViewOut,
        status.NOT_FOUND: global_schemas.NotFoundError,
    },
    exclude_none=True,
)
def patch_promocode(
    request: HttpRequest,
    promocode_id: str,
    patched_fields: schemas.PatchPromocodeIn,
) -> schemas.PromocodeViewOut:
    business = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id).select_related(
        "target", "business"
    )

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.annotate(
        used_count=Count("activations"),
        like_count=Count("likes"),
    )

    promocode = promocodes.first()

    if promocode.business != business:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    patch_data = patched_fields.dict(exclude_unset=True)
    target_data = patch_data.pop("target", None)

    for field, value in patch_data.items():
        setattr(promocode, field, value)

    if target_data:
        for field, value in target_data.items():
            setattr(promocode.target, field, value)
        if "country" in target_data:
            promocode.target.country_raw = target_data["country"]
        promocode.target.save()

    promocode.save()

    return utils.map_promocode_to_schema(promocode)


@router.get(
    "/promo/{promocode_id}/stat",
    auth=BusinessAuth(),
    response={
        status.OK: schemas.PromocodeStats,
        status.NOT_FOUND: global_schemas.NotFoundError,
    },
    exclude_none=True,
)
def promocode_stat(
    request: HttpRequest, promocode_id: str
) -> schemas.PromocodeStats:
    business = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id).prefetch_related(
        "activations",
    )

    if not promocodes.exists():
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes.prefetch_related("activations__user")
    promocode = promocodes.first()

    if promocode.business != business:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    activations = promocode.activations.all()
    activations_count = activations.count()

    country_activations = Counter(
        activation.user.country.code
        for activation in activations
        if activation.user.country
    )

    sorted_countries = sorted(country_activations.items(), key=lambda x: x[0])

    return status.OK, schemas.PromocodeStats(
        activations_count=activations_count,
        countries=[
            schemas.PromocodeStatsForCountry(
                country=country, activations_count=count
            )
            for country, count in sorted_countries
        ]
        if country_activations.items()
        else None,
    )
