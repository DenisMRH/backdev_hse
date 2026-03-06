from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL


def _endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, exclude_paths: set[str] | None = None):
        super().__init__(app)
        self._exclude_paths = exclude_paths or set()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        endpoint = "unknown"
        try:
            response = await call_next(request)
            status_code = response.status_code
            endpoint = _endpoint_label(request)
            return response
        finally:
            elapsed = time.perf_counter() - start
            method = request.method
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(elapsed)
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
