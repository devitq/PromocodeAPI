import datetime
from http import HTTPStatus as status

from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from ninja import Query, Router
from ninja.errors import AuthenticationError, HttpError

from api.v1 import schemas as global_schemas
from api.v1.auth import BusinessAuth
from api.v1.business import schemas
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

    target_obj = PromocodeTarget(**target)
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

    promocodes = Promocode.objects.filter(business=business)

    if filters.country__in:
        promocodes = promocodes.filter(
            Q(target__country__in=filters.country__in)
            | Q(target__country__isnull=True)
        )

    if filters.query == "active_from":
        promocodes = promocodes.annotate(
            active_from_sort=Coalesce("active_from", Value(datetime.min))
        ).order_by("-active_from_sort")
    elif filters.query == "active_until":
        promocodes = promocodes.annotate(
            active_until_sort=Coalesce("active_until", Value(datetime.max))
        ).order_by("-active_until_sort")
    else:
        promocodes = promocodes.order_by("-created_at")

    promocodes = promocodes.annotate(
        used_count=Count("activations"),
        like_count=Count("comments"),
    )

    response["X-Total-Count"] = promocodes.count()

    promocodes = promocodes[filters.offset : filters.offset + filters.limit]

    return [
        schemas.PromocodeViewOut(
            promo_id=promocode.id,
            company_id=promocode.business.id,
            company_name=promocode.business.name,
            description=promocode.description,
            image_url=promocode.image_url,
            target=schemas.PromocodeTargetViewOut(
                age_from=promocode.target.age_from,
                age_until=promocode.target.age_until,
                country=promocode.target.country.code
                if promocode.target.country
                else None,
                categories=promocode.target.categories,
            ),
            max_count=promocode.max_count,
            active_from=promocode.active_from,
            active_until=promocode.active_until,
            mode=promocode.mode,
            promo_common=promocode.promo_common,
            promo_unique=promocode.promo_unique,
            like_count=promocode.like_count,
            used_count=promocode.used_count,
            active=promocode.active,
        )
        for promocode in promocodes
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
def product_get(
    request: HttpRequest, promocode_id: str
) -> schemas.PromocodeViewOut:
    business = request.auth

    promocodes = Promocode.objects.filter(id=promocode_id)

    if len(promocodes) == 0:
        raise HttpError(status.NOT_FOUND, status.NOT_FOUND.phrase)

    promocodes = promocodes.annotate(
        used_count=Count("activations"),
        like_count=Count("comments"),
    )

    promocode = promocodes[0]

    if promocode.business != business:
        raise HttpError(status.FORBIDDEN, status.FORBIDDEN.phrase)

    return schemas.PromocodeViewOut(
        promo_id=promocode.id,
        company_id=promocode.business.id,
        company_name=promocode.business.name,
        description=promocode.description,
        image_url=promocode.image_url,
        target=schemas.PromocodeTargetViewOut(
            age_from=promocode.target.age_from,
            age_until=promocode.target.age_until,
            country=promocode.target.country.code
            if promocode.target.country
            else None,
            categories=promocode.target.categories,
        ),
        max_count=promocode.max_count,
        active_from=promocode.active_from,
        active_until=promocode.active_until,
        mode=promocode.mode,
        promo_common=promocode.promo_common,
        promo_unique=promocode.promo_unique,
        like_count=promocode.like_count,
        used_count=promocode.used_count,
        active=promocode.active,
    )
