from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from user_agents import parse


@dataclass(frozen=True)
class LocationContext:
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: Optional[str] = None


@dataclass(frozen=True)
class UserContext:
    ip: str
    device: str
    os: str
    browser: str
    user_agent: str
    location: LocationContext
    timestamp: datetime
    request_id: str


class UserContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)

        context = UserContext(
            ip=self._get_client_ip(request),
            device=self._get_device(user_agent),
            os=self._get_os(user_agent),
            browser=self._get_browser(user_agent),
            user_agent=user_agent_string,
            location=LocationContext(),
            timestamp=datetime.now(timezone.utc),
            request_id=str(uuid4()),
        )

        request.state.context = context

        response = await call_next(request)

        response.headers["X-Request-ID"] = context.request_id

        return response

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
    def _get_os(user_agent) -> str:
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