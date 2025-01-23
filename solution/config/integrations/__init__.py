from datetime import datetime
from http import HTTPStatus as status
from typing import ClassVar

import httpx
from django.core.cache import cache
from django.utils import timezone


class AntifraudServiceInteractor:
    HEADERS: ClassVar[dict[str, str]] = {"Content-Type": "application/json"}
    CACHE_PREFIX = "antifraud_cache"

    def __init__(self, endpoint: str) -> None:
        self.antifraud_endpoint = f"{endpoint}/api/validate"

    @classmethod
    def get_cache_key(cls, user_email: str, promo_id: str) -> None:
        return f"{cls.CACHE_PREFIX}:{user_email}:{promo_id}"

    @classmethod
    def is_cache_valid(cls, cache_until: str) -> bool:
        if cache_until:
            return (
                datetime.fromisoformat(cache_until).replace(
                    tzinfo=timezone.utc,
                )
                > timezone.now()
            )
        return False

    @classmethod
    def validate(cls, user_email: str, promo_id: str) -> dict[str, bool | str]:
        cache_key = cls.get_cache_key(user_email, promo_id)
        cached_result = cache.get(cache_key)

        if cached_result and cls.is_cache_valid(
            cached_result.get("cache_until"),
        ):
            return cached_result

        payload = {"user_email": user_email, "promo_id": promo_id}
        try:
            with httpx.Client(timeout=5) as client:
                response = client.post(
                    cls.antifraud_endpoint,
                    json=payload,
                    headers=cls.HEADERS,
                )

                if response.status_code == status.OK:
                    result = response.json()

                    if "cache_until" in result:
                        cache.set(cache_key, result)

                    return result

                retry_response = client.post(
                    cls.antifraud_endpoint,
                    json=payload,
                    headers=cls.HEADERS,
                )
                if retry_response.status_code == status.OK:
                    result = retry_response.json()
                    if "cache_until" in result:
                        cache.set(cache_key, result)
                    return result

        except httpx.HTTPError:
            pass

        return {"ok": False}
