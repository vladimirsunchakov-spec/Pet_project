from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("_request_id", default="")

def get_request_id() -> str:
    return request_id_var.get()

def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid4()))
        request.id = request_id
        request.state.request_id = request_id

        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            request_id_var.reset(token)