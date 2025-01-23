from django.contrib import admin

from apps.promo.models import (
    Promocode,
    PromocodeActivation,
    PromocodeComment,
    PromocodeLike,
    PromocodeTarget,
)

admin.site.register(Promocode)
admin.site.register(PromocodeTarget)
admin.site.register(PromocodeActivation)
admin.site.register(PromocodeComment)
admin.site.register(PromocodeLike)
