from prometheus_client import Counter, Histogram, Gauge
import time
from typing import Callable
from functools import wraps

# Metrics
REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['endpoint']
)

ACTIVE_USERS = Gauge(
    'app_active_users',
    'Number of active users'
)

FILE_UPLOAD_SIZE = Histogram(
    'app_file_upload_size_bytes',
    'File Upload Size in Bytes',
    buckets=[1024 * 1024 * x for x in [1, 5, 10, 50, 100]]  # 1MB to 100MB buckets
)


def track_metrics(func: Callable):
    """Decorator to track endpoint metrics"""

    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()

        try:
            response = await func(request, *args, **kwargs)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            duration = time.time() - start_time
            endpoint = request.url.path
            REQUEST_COUNT.labels(endpoint=endpoint, method=request.method, status=status).inc()
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        return response

    return wrapper