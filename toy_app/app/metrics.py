"""
Custom Prometheus metrics for bug detection.

These metrics expose the three intentional bugs:
1. Memory leak (growing cache)
2. N+1 query (DB connection exhaustion)
3. Payment service failures
"""

from prometheus_client import Counter, Gauge, Histogram

# Memory leak metrics
product_cache_entries = Gauge(
    "product_cache_entries_total",
    "Number of entries in product cache (memory leak indicator)",
)
product_analytics_entries = Gauge(
    "product_analytics_entries_total",
    "Number of analytics entries (memory leak indicator)",
)
estimated_leak_memory_bytes = Gauge(
    "estimated_leak_memory_bytes",
    "Estimated memory consumed by leaked caches in bytes",
)

# Payment metrics
payment_requests_total = Counter(
    "payment_requests_total",
    "Total payment requests",
    ["status", "operation"],
)
payment_request_duration_seconds = Histogram(
    "payment_request_duration_seconds",
    "Payment request duration in seconds",
    ["operation"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# DB pool metrics
db_pool_connections_active = Gauge(
    "db_pool_connections_active",
    "Number of active DB pool connections",
)
db_pool_connections_idle = Gauge(
    "db_pool_connections_idle",
    "Number of idle DB pool connections",
)
db_pool_overflow = Gauge(
    "db_pool_overflow",
    "Number of overflow connections in use",
)
