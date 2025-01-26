from api.v1.user import schemas
from apps.promo.models import Promocode, PromocodeComment
from apps.user.models import User


def map_user_to_schema(user: User) -> schemas.ViewUserOut:
    return schemas.ViewUserOut(
        name=user.name,
        surname=user.surname,
        email=user.email,
        avatar_url=user.avatar_url,
        other=schemas.UserTarget(
            age=user.age,
            country=user.country_raw,
        ),
    )


def map_promocode_to_schema(promocode: Promocode) -> schemas.PromocodeViewOut:
    return schemas.PromocodeViewOut(
        promo_id=promocode.id,
        company_id=promocode.business.id,
        company_name=promocode.business.name,
        description=promocode.description,
        image_url=promocode.image_url,
        is_activated_by_user=promocode.is_activated_by_user,
        is_liked_by_user=promocode.is_liked_by_user,
        like_count=promocode.like_count,
        comment_count=promocode.comment_count,
        active=promocode.active,
    )


def map_comment_to_schema(comment: PromocodeComment) -> schemas.CommentOut:
    return schemas.CommentOut(
        id=comment.id,
        text=comment.text,
        date=comment.date,
        author=schemas.CommentAuthor(
            name=comment.author.name,
            surname=comment.author.surname,
            avatar_url=comment.author.avatar_url,
        ),
    )
