"""Allowlisted request diagnostics. Financial payloads never enter log records."""
from contextvars import ContextVar
import json
import logging
import re
import sys
from time import perf_counter
from uuid import UUID, uuid4

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

correlation_id: ContextVar[str | None] = ContextVar('vela_correlation_id', default=None)
_HEX = re.compile(r'[a-fA-F0-9]{16,64}\Z')
_ROUTE = re.compile(r'/[A-Za-z0-9_/{.}-]*\Z')
_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}


def safe_correlation_id(value):
    """Only opaque IDs, never free-text customer names/emails or control characters."""
    if isinstance(value, str) and len(value) <= 64:
        if _HEX.fullmatch(value):
            return value
        try:
            parsed = UUID(value)
            if str(parsed) == value.lower():
                return value
        except ValueError:
            pass
    return str(uuid4())


class RequestPrivacyFilter(logging.Filter):
    """Drop non-request events and replace all arbitrary message/exception content."""
    def filter(self, record):
        if getattr(record, 'event', None) != 'http_request':
            return False
        record.msg, record.args = 'http_request', ()
        record.exc_info, record.exc_text, record.stack_info = None, None, None
        return True


class RequestJSONFormatter(logging.Formatter):
    def format(self, record):
        # Do not serialize record.__dict__, getMessage(), extra fields or traceback.
        route = getattr(record, 'route', None)
        method = getattr(record, 'method', None)
        status = getattr(record, 'status', 500)
        elapsed = getattr(record, 'duration_ms', 0)
        return json.dumps({
            'event': 'http_request',
            'correlation_id': safe_correlation_id(getattr(record, 'correlation_id', None)),
            'method': method if method in _METHODS else 'OTHER',
            'route': route if isinstance(route, str) and _ROUTE.fullmatch(route) else 'unmatched',
            'status': status if isinstance(status, int) and 100 <= status <= 599 else 500,
            'duration_ms': elapsed if isinstance(elapsed, int) and elapsed >= 0 else 0,
        }, separators=(',', ':'))


class CorrelationMiddleware:
    def __init__(self, app, logger):
        self.app, self.logger = app, logger

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        values = [value for key, value in scope.get('headers', []) if key.lower() == b'x-correlation-id']
        supplied = values[0].decode('latin-1') if len(values) == 1 else None
        current = safe_correlation_id(supplied)
        token = correlation_id.set(current)
        scope.setdefault('state', {})['correlation_id'] = current
        status, started = 500, perf_counter()

        async def correlated_send(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                MutableHeaders(scope=message)['X-Correlation-ID'] = current
            await send(message)

        try:
            await self.app(scope, receive, correlated_send)
        finally:
            try:
                route = getattr(scope.get('route'), 'path', None)
                self.logger.info('http_request', extra={
                    'event': 'http_request', 'correlation_id': current,
                    'method': scope.get('method'), 'route': route,
                    'status': status, 'duration_ms': max(0, int((perf_counter()-started)*1000)),
                })
            finally:
                correlation_id.reset(token)


def install_request_logging(app, frontend_origins):
    # A private logger per factory instance: no global registry/root/uvicorn changes.
    logger = logging.Logger('vela.request', level=logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestPrivacyFilter())
    handler.setFormatter(RequestJSONFormatter())
    logger.addHandler(handler)
    app.state.request_logger = logger
    app.add_middleware(CorrelationMiddleware, logger=logger)
    allowed_origins = frozenset(frontend_origins)

    async def unhandled_error(request, exc):
        # ServerErrorMiddleware owns unexpected500s outside user middleware.
        # ContextVar has reset by then; request.state retains this request's ID.
        current = getattr(request.state, 'correlation_id', None)
        headers = {'X-Correlation-ID': safe_correlation_id(current), 'Vary': 'Origin'}
        origin = request.headers.get('origin')
        if origin in allowed_origins:
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Expose-Headers'] = 'X-Correlation-ID'
        return JSONResponse({'detail': 'The server could not complete this request.'}, status_code=500,
                            headers=headers)
    app.add_exception_handler(Exception, unhandled_error)
