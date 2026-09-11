import logging
from dataclasses import asdict

from fastapi import FastAPI, Request

from app.auth.router import router as auth_router
from app.config import settings
from app.core.logging import setup_logging
from app.core.middleware import UserContextMiddleware
from app.vehicles.router import router as vehicles_router

setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vehicle Management API",
    version="1.0.0",
    description="Secure vehicle management backend with Google OAuth, RBAC, and refresh token rotation",
)

app.add_middleware(UserContextMiddleware)

api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(vehicles_router, prefix=api_prefix)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("FastAPI application started", extra={"event": "startup"})


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("FastAPI application shutting down", extra={"event": "shutdown"})


@app.get("/")
def read_root():
    return {"message": "Vehicle Management API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness_check():
    return {"status": "ready"}


@app.get("/debug/context")
async def debug_context(request: Request):
    return asdict(request.state.context)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
