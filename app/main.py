import logging
from dataclasses import asdict

from fastapi import FastAPI, Request

from app.auth.router import router as auth_router
from app.config import settings
from app.core.logging import setup_logging
from app.core.middleware import UserContextMiddleware

setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(UserContextMiddleware)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("FastAPI application started", extra={"event": "startup"})


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("FastAPI application shutting down", extra={"event": "shutdown"})


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/debug/context")
async def debug_context(request: Request):
    return asdict(request.state.context)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)