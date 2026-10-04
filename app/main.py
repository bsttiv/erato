import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from app.core.errors import AppError, DatabaseConnectionError, InternalError
from app.routers import (
    auth,
    compositions,
    demos,
    entitlements,
    health,
    history,
    maintenance,
    sections,
    sharing,
)

logger = logging.getLogger("erato")







app = FastAPI(
    title="Erato API",
    description="Backend API for Erato band songwriting and composition management",
    version="0.1.0",
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle domain errors with declared HTTP status and structured payload."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors without leaking internal stack traces."""
    clean_details = [
        {
            "loc": list(e.get("loc", [])),
            "msg": e.get("msg", ""),
            "type": e.get("type", ""),
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Datos de solicitud inválidos",
            "detail": "Datos de solicitud inválidos",
            "details": clean_details,
        },
    )



@app.exception_handler(PyMongoError)
async def mongo_exception_handler(request: Request, exc: PyMongoError) -> JSONResponse:
    """Handle database errors without leaking internal connection or host details."""
    logger.error("Database error occurred: %s", exc)
    if isinstance(exc, (ServerSelectionTimeoutError, ConnectionFailure)):
        err: AppError = DatabaseConnectionError()
    else:
        err = InternalError(message="Error en el servicio de datos")
    return JSONResponse(
        status_code=err.status_code,
        content=err.to_dict(),
    )


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions, returning a safe 500 without leaking internals."""
    logger.exception("Unhandled server error: %s", exc)
    internal_err = InternalError()
    return JSONResponse(
        status_code=internal_err.status_code,
        content=internal_err.to_dict(),
    )


# Routers
app.include_router(health.router)
app.include_router(maintenance.router)
app.include_router(auth.router)
app.include_router(compositions.router)
app.include_router(sections.router)
app.include_router(sharing.router)
app.include_router(demos.router)
app.include_router(entitlements.router)
app.include_router(history.router)



# - app.include_router(demos.router)          # Unit 4
