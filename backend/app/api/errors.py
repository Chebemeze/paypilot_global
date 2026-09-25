"""
PayPilot Global — Unified error handling.

Owner: Person 1 (Backend Core — Auth & Employees)

WHY THIS FILE EXISTS
--------------------
Out of the box a FastAPI app answers errors in three different shapes:

    1. raise HTTPException(404, "Not found")
       -> {"detail": "Not found"}                       (a string)

    2. Pydantic validation failure
       -> {"detail": [{"loc": [...], "msg": ...}, ...]} (a list)

    3. An unhandled crash
       -> a text/html stack-trace page, status 500      (not even JSON)

The frontend therefore needs three different parsers, and case 3 leaks internal
file paths and SQL to the browser. This module collapses all three into one
predictable envelope.

THE ENVELOPE
------------
    {
      "error": {
        "code":       "VALIDATION_ERROR",   # stable, machine-readable
        "message":    "…",                  # safe to show a user
        "status":     422,
        "fields":     [ {"field": "email", "message": "…"} ],   # optional
        "request_id": "a1b2c3d4"            # matches the X-Request-ID header
      },
      "detail": "…"                          # legacy mirror of .message
    }

`detail` is kept on purpose so existing frontend code that reads `err.detail`
keeps working. It will be removed once Person 3 and Person 4 have migrated.

REGISTRATION
------------
    from app.api.errors import register_exception_handlers
    register_exception_handlers(app)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("paypilot.errors")


# ─── Status code -> stable error code ─────────────────────────────────────────
# The frontend should branch on these strings, never on the human message
# (messages get reworded; codes are a contract).

STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "UPSTREAM_ERROR",
    503: "SERVICE_UNAVAILABLE",
    504: "UPSTREAM_TIMEOUT",
}

#: Shown instead of the real exception text when something unexpected breaks.
GENERIC_500_MESSAGE = (
    "Something went wrong on our side. "
    "Quote the request id if you contact support."
)


def _request_id(request: Request) -> str:
    """Read the id set by the request-id middleware in main.py."""
    return getattr(request.state, "request_id", "")


def build_error_response(
    status_code: int,
    message: str,
    *,
    request: Optional[Request] = None,
    code: Optional[str] = None,
    fields: Optional[list[dict[str, Any]]] = None,
    headers: Optional[dict[str, str]] = None,
) -> JSONResponse:
    """Construct the one and only error envelope this API emits."""
    error: dict[str, Any] = {
        "code": code or STATUS_TO_CODE.get(status_code, "ERROR"),
        "message": message,
        "status": status_code,
    }
    if fields:
        error["fields"] = fields

    out_headers = dict(headers or {})

    if request is not None:
        rid = _request_id(request)
        error["request_id"] = rid
        # Set the header here too. A 500 is handled by Starlette's outermost
        # ServerErrorMiddleware, which sits ABOVE our request-id middleware in
        # main.py — so that middleware never gets to add the header on a crash.
        # Without this line the one response you most need to trace is the one
        # response missing its trace id.
        if rid:
            out_headers.setdefault("X-Request-ID", rid)

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"error": error, "detail": message}),
        headers=out_headers or None,
    )


# ─── Custom exception for richer, intentional errors ──────────────────────────

class AppError(Exception):
    """Raise this when you want to control the error code explicitly.

        raise AppError(409, "That email is taken.", code="EMAIL_TAKEN")

    Plain `HTTPException` still works everywhere and is mapped automatically —
    this is only for when the status code alone isn't specific enough.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: Optional[str] = None,
        fields: Optional[list[dict[str, Any]]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.fields = fields
        self.headers = headers


# ─── Handlers ─────────────────────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return build_error_response(
        exc.status_code, exc.message,
        request=request, code=exc.code, fields=exc.fields, headers=exc.headers,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Normalise every `raise HTTPException(...)` in the codebase.

    All 34 existing raise sites keep working untouched — they just come out the
    other side in the standard envelope.
    """
    detail = exc.detail

    # HTTPException(detail=...) is usually a string, but can be any JSON value.
    if isinstance(detail, str):
        message = detail
        fields = None
    elif isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Request failed.")
        fields = detail.get("fields")
    else:
        message = str(detail)
        fields = None

    return build_error_response(
        exc.status_code, message,
        request=request,
        fields=fields,
        headers=getattr(exc, "headers", None),  # preserves WWW-Authenticate on 401
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Flatten Pydantic's nested error list into `fields`.

    Pydantic gives us:
        {"loc": ["body", "email"], "msg": "Value error, '…' is not valid", ...}

    The frontend wants:
        {"field": "email", "message": "'…' is not valid"}

    so it can attach the message to the right form input.
    """
    fields: list[dict[str, Any]] = []

    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", [])]
        # Drop the source prefix ("body" / "query" / "path") — the frontend
        # cares about the field name, not where FastAPI found it.
        source = loc[0] if loc else "body"
        parts = loc[1:] if loc and loc[0] in ("body", "query", "path", "header", "cookie") else loc
        field = ".".join(parts) if parts else source

        # Pydantic prefixes custom validator messages with "Value error, ".
        msg = str(err.get("msg", "Invalid value"))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]

        fields.append({"field": field, "message": msg, "type": err.get("type", "")})

    if len(fields) == 1:
        message = f"{fields[0]['field']}: {fields[0]['message']}"
    else:
        names = ", ".join(f["field"] for f in fields)
        message = f"Validation failed for {len(fields)} fields: {names}."

    return build_error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY, message,
        request=request, code="VALIDATION_ERROR", fields=fields,
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """A database constraint was violated — usually a duplicate unique value.

    Endpoints should check for duplicates explicitly and return a friendly 409,
    but this is the safety net for the race where two requests pass the check at
    the same moment. Returning 500 for that would be wrong: the client's request
    genuinely conflicted, so 409 is the honest answer.
    """
    logger.warning(
        "IntegrityError on %s %s [%s]: %s",
        request.method, request.url.path, _request_id(request), exc.orig,
    )
    return build_error_response(
        status.HTTP_409_CONFLICT,
        "That record conflicts with one that already exists.",
        request=request, code="CONFLICT",
    )


async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Any other database failure. Log the real cause, tell the client nothing.

    A raw SQLAlchemy message can contain table names, column names and even row
    values — that is reconnaissance material for an attacker.
    """
    logger.exception(
        "Database error on %s %s [%s]",
        request.method, request.url.path, _request_id(request),
    )
    return build_error_response(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "The database is temporarily unavailable. Please try again.",
        request=request, code="DATABASE_ERROR",
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Last line of defence: turn any crash into clean JSON.

    The full traceback goes to the server log, indexed by request_id. The client
    gets a generic message plus that id, so a user can report "request a1b2c3d4
    failed" and you can find the exact stack trace.
    """
    logger.exception(
        "Unhandled %s on %s %s [%s]",
        type(exc).__name__, request.method, request.url.path, _request_id(request),
    )
    return build_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        GENERIC_500_MESSAGE,
        request=request, code="INTERNAL_ERROR",
    )


# ─── Registration ─────────────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler. Call once from main.py, after the app is created.

    Order matters: more specific exception classes must be registered before
    the broad `Exception` catch-all.
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
