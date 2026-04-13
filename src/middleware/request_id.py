import uuid
from contextvars import ContextVar
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from exceptions import request_id
from exceptions.request_id import RequestIdNotSetError

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def get_request_id() -> str:
    request_id = request_id_var.get()
    if not request_id:
        raise RequestIdNotSetError()
    return request_id

def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.id = request.headers.get("X-Request-Id", str(uuid4()))
        request.state.request_id = request.id
        set_request_id(request.id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.id
        return response