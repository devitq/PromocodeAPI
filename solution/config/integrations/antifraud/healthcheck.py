from http import HTTPStatus as status

import httpx
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend


class AntifraudHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self) -> None:
        try:
            response = httpx.get(
                f"{settings.ANTIFRAUD_ADDRESS}/api/ping", timeout=1
            )
            if response.status_code >= status.INTERNAL_SERVER_ERROR:
                self.add_error("Antifraud service is unaccessible")
        except httpx.HTTPError:
            self.add_error("Antifraud service is unaccessible")

    def identifier(self) -> str:
        return self.__class__.__name__
