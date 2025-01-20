from http import HTTPStatus as status

from django.http import HttpRequest
from ninja import Router
from ninja.errors import AuthenticationError

from api.v1 import schemas as global_schemas
from api.v1.business import schemas
from apps.business.models import Business

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
    request: HttpRequest, business: schemas.BusinessSignUpIn
) -> tuple[int, schemas.BusinessSignUpOut]:
    business_obj = Business(**business.dict())
    business_obj.save()

    return status.OK, schemas.BusinessSignUpOut(
        token=business_obj.generate_token(), company_id=business_obj.id
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
    request: HttpRequest, login_data: schemas.BusinessSignInIn
) -> tuple[int, schemas.BusinessSignInOut]:
    try:
        business_obj = Business.objects.get(email=login_data.email)
    except Business.DoesNotExist:
        raise AuthenticationError from None

    if business_obj.password != login_data.password:
        raise AuthenticationError

    business_obj.token_version += 1
    business_obj.save()

    return status.OK, schemas.BusinessSignInOut(
        token=business_obj.generate_token()
    )
