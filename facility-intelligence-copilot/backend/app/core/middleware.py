from __future__ import annotations

import logging
import time
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.audit")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id or len(request_id) > 64:
            request_id = str(uuid4())

        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Audit logging for requests (excluding health polling to keep logs clean)
        if request.url.path not in {"/health", "/favicon.ico"}:
            client_ip = request.client.host if request.client else "unknown"
            logger.info(
                "AUDIT | request_id=%s method=%s path=%s status=%s duration_ms=%s client_ip=%s",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                client_ip,
            )

        return response
