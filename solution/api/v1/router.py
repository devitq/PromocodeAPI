from functools import partial

from ninja import NinjaAPI

from api.v1 import handlers
from api.v1.business.views import router as business_router
from api.v1.ping.views import router as ping_router
from api.v1.user.views import router as user_router

router = NinjaAPI(
    title="Promocode API",
    version="1",
    description="API docs for Promocode",
    openapi_url="/docs/openapi.json",
    # csrf=True, noqa: ERA001
)


# Register application's routers

router.add_router(
    "ping",
    ping_router,
)
router.add_router(
    "business",
    business_router,
)
router.add_router(
    "user",
    user_router,
)


# Register exception handlers

for exception, handler in handlers.exception_handlers:
    router.add_exception_handler(exception, partial(handler, router=router))
