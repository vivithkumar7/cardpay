import logging
import time

from django.conf import settings

from .monitoring import record_request

logger = logging.getLogger("api.monitoring")


class ApiRequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_threshold_ms = float(
            getattr(settings, "API_SLOW_REQUEST_THRESHOLD_MS", 1000)
        )

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        started = time.perf_counter()
        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "API request raised an exception method=%s path=%s duration_ms=%.2f",
                request.method,
                request.path,
                duration_ms,
            )
            record_request(500, duration_ms, self.slow_threshold_ms)
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        record_request(response.status_code, duration_ms, self.slow_threshold_ms)
        match = getattr(request, "resolver_match", None)
        callback = getattr(match, "func", None)
        view_class = getattr(callback, "view_class", None)
        view_name = view_class.__name__ if view_class else getattr(callback, "__name__", "unmatched")
        log = logger.error if response.status_code >= 500 else (
            logger.warning if response.status_code >= 400 else logger.info
        )
        log(
            "API request method=%s path=%s view=%s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            view_name,
            response.status_code,
            duration_ms,
        )
        if duration_ms >= self.slow_threshold_ms:
            logger.warning(
                "Slow API request method=%s path=%s status=%s duration_ms=%.2f",
                request.method,
                request.path,
                response.status_code,
                duration_ms,
            )
        return response
