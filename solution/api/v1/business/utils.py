from api.v1.business import schemas
from apps.promo.models import Promocode


def map_promocode_to_schema(promocode: Promocode) -> schemas.PromocodeViewOut:
    return schemas.PromocodeViewOut(
        promo_id=promocode.id,
        company_id=promocode.business.id,
        company_name=promocode.business.name,
        description=promocode.description,
        image_url=promocode.image_url,
        target=schemas.PromocodeTargetViewOut(
            age_from=promocode.target.age_from,
            age_until=promocode.target.age_until,
            country=promocode.target.country_raw
            if promocode.target.country_raw
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
