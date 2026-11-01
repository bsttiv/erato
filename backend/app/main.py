"""Erato's flat, synchronous HTTP application."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

import httpx
from pymongo import MongoClient
from starlette.concurrency import run_in_threadpool

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.config import load_config
from app.accounts import router
from app.database import create_indexes
from app.bands import router as bands_router
from app.songs import router as songs_router
from app.demos import router as demos_router
from app.errors import APIError


def create_app(*, clock=None, maestro_timeout=3.0):
    @asynccontextmanager
    async def lifespan(app):
        client = MongoClient(app.state.config["MONGODB_URI"], tz_aware=True,
                             serverSelectionTimeoutMS=5000)
        app.state.db = client[app.state.config["MONGODB_DB"]]
        try:
            await run_in_threadpool(create_indexes, app.state.db)
            with httpx.Client(base_url=app.state.config["MAESTRO_URL"].rstrip("/") + "/",
                              headers={"X-Api-Key": app.state.config["MAESTRO_API_KEY"]},
                              timeout=app.state.maestro_timeout) as maestro:
                app.state.maestro = maestro
                yield
        finally:
            client.close()

    app = FastAPI(title="Erato", lifespan=lifespan)
    app.state.config = load_config()
    app.state.clock = clock or (lambda: datetime.now(timezone.utc))
    app.state.maestro_timeout = maestro_timeout

    app.include_router(router)
    app.include_router(songs_router)
    app.include_router(bands_router)
    app.include_router(demos_router)

    @app.middleware("http")
    async def successful_access(request, call_next):
        response = await call_next(request)
        session = getattr(request.state, "session", None)
        if response.status_code < 400 and session is not None:
            now = app.state.clock()
            await run_in_threadpool(app.state.db.sessions.update_one, {
                "_id": session["_id"],
                "last_access_at": {"$lte": now - timedelta(minutes=1)},
            }, {"$set": {"last_access_at": now}})
        return response

    @app.exception_handler(APIError)
    async def api_error(request, exc):
        return JSONResponse(status_code=exc.status, headers=exc.headers, content={
            "code": exc.code, "detail": exc.code.replace("_", " ").capitalize(),
        })

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=422, content={
            "code": "validation_error", "detail": "Invalid request fields",
        })

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        codes = {401: "not_authenticated", 403: "forbidden", 404: "not_found",
                 422: "validation_error", 502: "session_upstream_error"}
        return JSONResponse(status_code=exc.status_code, headers=exc.headers, content={
            "code": codes.get(exc.status_code, "validation_error"), "detail": str(exc.detail),
        })

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
