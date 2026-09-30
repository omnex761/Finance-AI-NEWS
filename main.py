"""FinSimplify AI - FastAPI application entrypoint."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes.news import router as news_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("finsimplify.main")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered financial news simplification platform.",
    version="1.0.0",
)

# CORS is disabled by default because the frontend is served by this same
# FastAPI app (same-origin). It is only enabled when the operator explicitly
# configures an allowlist via CORS_ALLOWED_ORIGINS.
if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    logger.info("CORS enabled for origins: %s", settings.CORS_ALLOWED_ORIGINS)
else:
    logger.info("CORS disabled (same-origin frontend).")

app.include_router(news_router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean, non-leaky validation error messages."""
    errors = [
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"error": "Invalid request", "detail": errors})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler: never leak stack traces or internals to the client."""
    logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred."},
    )


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the frontend dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    return FileResponse(str(index_path))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
