import time
import uuid
from starlette.types import ASGIApp, Receive, Scope, Send
from src.core.logging import logger


class RequestIDAndLoggingMiddleware:
    """
    Pure ASGI middleware for high-performance correlation ID generation,
    response duration tracking, and structured request logging.
    Avoids BaseHTTPMiddleware task-group deadlocks.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode("latin1")
        if not request_id:
            request_id = str(uuid.uuid4())

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        start_time = time.perf_counter()
        status_code = [200]

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-request-id", request_id.encode("latin1")))
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                resp_headers.append((b"x-response-time-ms", str(duration_ms).encode("latin1")))
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            path = scope.get("path", "")
            method = scope.get("method", "")
            logger.info(
                f"{method} {path} -> {status_code[0]} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code[0],
                    "duration_ms": duration_ms
                }
            )
