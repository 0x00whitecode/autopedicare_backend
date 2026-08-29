import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from user_agents import parse

from app.auth.geolocation import get_location_from_ip
from app.core.context import LocationContext, UserContext
from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class UserContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)

        ip = self._get_client_ip(request)
        
        SKIP_GEOLOCATION_PATHS = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
        if request.url.path in SKIP_GEOLOCATION_PATHS:
            location = LocationContext()
        else:
            location = await get_location_from_ip(ip)

        context = UserContext(
            ip=ip,
            device=self._get_device(user_agent),
            os=self._get_os(user_agent),
            browser=self._get_browser(user_agent),
            user_agent=user_agent_string,
            location=location,
            timestamp=datetime.now(timezone.utc),
            request_id=str(uuid4()),
        )

        request.state.context = context
        request.state.request_id = context.request_id

        request_id_token = request_id_var.set(context.request_id)

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000)
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers["X-Request-ID"] = context.request_id
            return response
        except Exception:
            logger.exception(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise
        finally:
            request_id_var.reset(request_id_token)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    @staticmethod
    def _get_device(user_agent) -> str:
        if user_agent.is_mobile:
            return "mobile"

        if user_agent.is_tablet:
            return "tablet"

        if user_agent.is_pc:
            return "desktop"

        return "unknown"

    @staticmethod
    def _get_os(user_agent):
        family = user_agent.os.family

        if user_agent.os.version:
            version = ".".join(str(v) for v in user_agent.os.version)
            return f"{family} {version}"

        return family

    @staticmethod
    def _get_browser(user_agent) -> str:
        family = user_agent.browser.family

        if user_agent.browser.version:
            version = ".".join(str(v) for v in user_agent.browser.version)
            return f"{family} {version}"

        return family