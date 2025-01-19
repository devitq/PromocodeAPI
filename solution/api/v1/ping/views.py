from http import HTTPStatus as status

from django.http import HttpRequest
from ninja import Router

from api.v1.ping import schemas

router = Router(tags=["ping"])


@router.get(
    "",
    response={status.OK: schemas.PingOut},
    summary="Ping server",
)
def index(
    request: HttpRequest,
) -> schemas.PingOut:
    return schemas.PingOut(message_from_basement="АЛЕКСАНДР ШАХОВ Я ВАШ ФОНАТ")
