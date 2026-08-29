import json
import logging
from typing import Optional

import httpx

from app.config import settings
from app.core.context import LocationContext
from app.core.redis import redis_client

logger = logging.getLogger(__name__)
GEOLOCATION_CACHE_TTL = 60 * 60 * 24


async def get_location_from_ip(ip: str) -> LocationContext:

    if ip in {"127.0.0.1", "::1", "unknown"}:
        return LocationContext()

    cache_key = f"geo:{ip}"

    try:
        cached_location = await redis_client.get(cache_key)
    except Exception:
        logger.warning(
            "Geolocation cache unavailable; continuing without cache",
            extra={"event": "geo_cache_unavailable"},
        )
        cached_location = None

    if cached_location:
        try:
            location_data = json.loads(cached_location)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid geolocation cache payload received",
                extra={"event": "geo_cache_invalid"},
            )
            location_data = {}

        if location_data:
            logger.debug("Geolocation cache hit", extra={"event": "geo_cache_hit"})
            return LocationContext(
                country=location_data.get("country"),
                state=location_data.get("state"),
                city=location_data.get("city"),
                latitude=location_data.get("latitude"),
                longitude=location_data.get("longitude"),
                isp=location_data.get("isp"),
            )

    logger.debug("Geolocation cache miss", extra={"event": "geo_cache_miss"})

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.GEO_IP_API_URL.rstrip('/')}/{ip}/json",
                params={
                    "token": settings.IP_API_KEY,
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        logger.warning(
            "Geolocation provider unavailable; continuing with empty location",
            extra={"event": "geo_provider_unavailable"},
        )
        return LocationContext()

    if not isinstance(data, dict):
        logger.warning(
            "Invalid geolocation response received",
            extra={"event": "geo_response_invalid"},
        )
        return LocationContext()

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    loc = data.get("loc")

    if loc:
        try:
            lat, lon = loc.split(",")
            latitude = float(lat)
            longitude = float(lon)
        except (ValueError, AttributeError):
            logger.warning(
                "Invalid geolocation coordinates received",
                extra={"event": "geo_coordinates_invalid"},
            )

    location = LocationContext(
        country=data.get("country"),
        state=data.get("region"),
        city=data.get("city"),
        latitude=latitude,
        longitude=longitude,
        isp=data.get("org"),
    )

    location_data = {
        "country": location.country,
        "state": location.state,
        "city": location.city,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "isp": location.isp,
    }

    try:
        await redis_client.setex(
            cache_key,
            GEOLOCATION_CACHE_TTL,
            json.dumps(location_data),
        )
    except Exception:
        logger.warning(
            "Geolocation cache write failed; request can continue",
            extra={"event": "geo_cache_write_failed"},
        )

    return location
