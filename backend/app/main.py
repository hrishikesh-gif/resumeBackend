from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import models
from .config import AUTO_CREATE_TABLES, CORS_ALLOW_ORIGINS
from .database import Base, engine
from .routes import auth_routes
from app.routes import resume_routes


app = FastAPI(openapi_version="3.0.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(resume_routes.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )

    body_schema = schema.get("components", {}).get("schemas", {}).get(
        "Body_analyze_resumes_resumes_analyze_post"
    )
    if body_schema:
        files_prop = body_schema.get("properties", {}).get("files", {})
        items = files_prop.get("items", {})
        if items.get("contentMediaType") == "application/octet-stream":
            items.pop("contentMediaType", None)
            items["format"] = "binary"
            files_prop["items"] = items

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def read_root():
    return {"message": "Backend is running successfully"}


@app.get("/health")
def health():
    return {"status": "ok"}


def _status_to_code(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
    }
    return mapping.get(status_code, "http_error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "detail" in detail and "code" in detail:
        payload = detail
    elif isinstance(detail, str):
        payload = {"detail": detail, "code": _status_to_code(exc.status_code)}
    else:
        payload = {"detail": "Request failed", "code": _status_to_code(exc.status_code)}
    return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "validation_error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )
