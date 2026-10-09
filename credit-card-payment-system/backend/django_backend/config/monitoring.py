import threading
import time
from collections import Counter


_started_at = time.time()
_lock = threading.Lock()
_request_count = 0
_failure_count = 0
_slow_request_count = 0
_total_duration_ms = 0.0
_status_counts = Counter()


def record_request(status_code, duration_ms, slow_threshold_ms):
    global _request_count, _failure_count, _slow_request_count, _total_duration_ms
    with _lock:
        _request_count += 1
        _total_duration_ms += duration_ms
        _status_counts[str(status_code)] += 1
        if status_code >= 400:
            _failure_count += 1
        if duration_ms >= slow_threshold_ms:
            _slow_request_count += 1


def get_health_snapshot():
    with _lock:
        return {
            "uptime_seconds": max(0, int(time.time() - _started_at)),
            "api_requests": _request_count,
            "api_failures": _failure_count,
            "slow_requests": _slow_request_count,
            "average_response_time_ms": (
                round(_total_duration_ms / _request_count, 2)
                if _request_count
                else 0.0
            ),
            "status_counts": dict(_status_counts),
        }
