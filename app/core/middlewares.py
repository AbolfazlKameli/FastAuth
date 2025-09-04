from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

request_object: ContextVar[Request] = ContextVar('request')


class PaginationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = request_object.set(request)
        try:
            response = await call_next(request)
        finally:
            request_object.reset(token)
        return response


def register_middlewares(app):
    app.add_middleware(PaginationMiddleware)
