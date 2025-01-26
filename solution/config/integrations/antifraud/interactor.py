import time
from datetime import datetime
from http import HTTPStatus as status
from typing import ClassVar

import httpx
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from pytz import timezone as tz

logger = settings.LOGGER


class AntifraudServiceInteractor:
    HEADERS: ClassVar[dict[str, str]] = {"Content-Type": "application/json"}
    CACHE_PREFIX = "antifraud_cache"
    ANTIFRAUD_ENDPOINT = f"{settings.ANTIFRAUD_ADDRESS}/api/validate"
    RETRY_COUNT: ClassVar[int] = 2

    @classmethod
    def get_cache_key(cls, user_email: str, promo_id: str) -> str:
        return f"{cls.CACHE_PREFIX}:{user_email}:{promo_id}"

    @classmethod
    def is_cache_valid(cls, cache_until: str) -> bool:
        if cache_until:
            try:
                cache_expiry = datetime.fromisoformat(cache_until).astimezone(
                    tz(settings.TIME_ZONE)
                )
                return cache_expiry > timezone.now()
            except ValueError:
                return False
        return False

    @staticmethod
    def _make_request(
        client: httpx.Client,
        url: str,
        payload: dict[str, str],
        headers: dict[str, str],
        retries: int,
    ) -> httpx.Response | None:
        for attempt in range(1, retries + 1):
            start_time = time.time()
            try:
                response = client.post(url, json=payload, headers=headers)
                request_time = time.time() - start_time
                logger.info(
                    "Attempt %d: Request to %s took %s seconds",
                    attempt,
                    url,
                    request_time,
                )

                if response.status_code == status.OK:
                    return response

                logger.warning(
                    "Attempt %d failed with status %d",
                    attempt,
                    response.status_code,
                )
            except httpx.HTTPError:
                logger.exception(
                    "Attempt %d: HTTP error during request to %s",
                    attempt,
                    url,
                )

        logger.exception("All %d attempts to %s failed", retries, url)
        return None

    @classmethod
    def validate(cls, user_email: str, promo_id: str) -> dict[str, bool | str]:
        cache_key = cls.get_cache_key(user_email, promo_id)
        cached_result = cache.get(cache_key)

        if cached_result and cls.is_cache_valid(
            cached_result.get("cache_until")
        ):
            return cached_result

        payload = {"user_email": user_email, "promo_id": promo_id}
        try:
            logger.info("Trying to validate antifraud")
            with httpx.Client(timeout=5) as client:
                response = cls._make_request(
                    client,
                    cls.ANTIFRAUD_ENDPOINT,
                    payload,
                    cls.HEADERS,
                    retries=cls.RETRY_COUNT,
                )

                if response:
                    logger.info("Antifraud works perfectly")
                    result = response.json()

                    if "cache_until" in result:
                        cache.set(cache_key, result)

                    return result

        except Exception as e:
            logger.exception(
                "Unexpected error during antifraud validation: %s",
                e,  # noqa: TRY401
            )

        return {"ok": False}
