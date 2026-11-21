"""Error answers: JSON under /api, the error page everywhere else."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.exceptions import HTTPException

from .deps import render_page

log = logging.getLogger("app")


def _api(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def _page(request: Request, status: int) -> Response:
    try:
        return render_page(request, "error.html", status)
    except Exception:  # the error page itself must never fail
        log.exception("error page failed")
        return HTMLResponse(f"<h1>{status}</h1>", status_code=status)


async def http_error(request: Request, exc: HTTPException) -> Response:
    headers = {"Retry-After": "60"} if exc.status_code in (429, 503) else None
    if _api(request):
        return JSONResponse({"detail": exc.detail}, exc.status_code, headers=headers)
    response = _page(request, exc.status_code)
    response.headers.update(headers or {})
    return response


async def invalid(request: Request, exc: RequestValidationError) -> Response:
    # Never echo the submitted input back (FastAPI's default does): only which fields failed.
    fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
    return JSONResponse({"detail": "invalid input", "fields": fields}, 422) if _api(request) else _page(request, 400)


async def crash(request: Request, exc: Exception) -> Response:
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "server error"}, 500) if _api(request) else _page(request, 500)


type Handler = Callable[[Request, Any], Coroutine[Any, Any, Response]]

# FastAPI(exception_handlers=…)
HANDLERS: dict[int | type[Exception], Handler] = {HTTPException: http_error, RequestValidationError: invalid, Exception: crash}
