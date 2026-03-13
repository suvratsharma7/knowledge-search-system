"""
Request-logging middleware for the Knowledge Search API.

Emits structured JSON logs to stdout for every HTTP request, and adds an
``X-Request-ID`` header to every response.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Logger — writes structured JSON to stdout
# ---------------------------------------------------------------------------

logger = logging.getLogger("knowledge_search.requests")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request as a single-line JSON object and inject
    ``X-Request-ID`` into the response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        t0 = time.perf_counter()

        response = await call_next(request)

        latency_ms = (time.perf_counter() - t0) * 1000.0

        log_entry: dict[str, Any] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))

        response.headers["X-Request-ID"] = request_id
        return response
