from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
from src.core.request_id import set_request_id

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.id = request.headers.get("X-Request-Id", str(uuid4()))
        request.state.request_id = request.id
        set_request_id(request.id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.id
        return response