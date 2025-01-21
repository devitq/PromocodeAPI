from django.contrib import admin

from apps.promo.models import Promocode, PromocodeTarget

admin.site.register(Promocode)
admin.site.register(PromocodeTarget)
