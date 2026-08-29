from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests
from google.oauth2 import id_token
import logging

logger = logging.getLogger(__name__)

from app.config import settings


def _verify_google_token_sync(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        return {
            "provider_id": idinfo["sub"],
            "email": idinfo.get("email"),
            "email_verified": idinfo.get("email_verified", False),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
        }
    except ValueError as exc:
        logger.warning(
            "Google ID token verification failed",
            extra={
                "provider": "google",
                "event": "google_token_verification_failed",
            },
        )

        logger.debug(
            "Google verification error: %s",
            str(exc),
        )
        raise ValueError("Invalid Google ID token") from exc

async def verify_google_token(token: str) -> dict:
    return await run_in_threadpool(
        _verify_google_token_sync,
        token,
    )