from dataclasses import asdict

from fastapi import FastAPI, Request

from app.core.middleware import UserContextMiddleware


app = FastAPI()

app.add_middleware(UserContextMiddleware)


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