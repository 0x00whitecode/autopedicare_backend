from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


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
