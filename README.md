# Sentinel E-Commerce API

A FastAPI-based e-commerce API with Prometheus/Grafana monitoring.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Services will be available at:
- **API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

To stop all services:
```bash
docker-compose down
```

## Making Requests

### Health Check
```bash
curl http://localhost:8000/health
```

### List Products
```bash
# Basic request
curl http://localhost:8000/products

# With pagination
curl "http://localhost:8000/products?page=1&page_size=10"

# With filters
curl "http://localhost:8000/products?min_price=10&max_price=100&in_stock=true"
```

### Get Single Product
```bash
curl http://localhost:8000/products/1
```

### Checkout
```bash
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 2}],
    "card_token": "tok_visa_123"
  }'
```

### Debug Endpoints
```bash
# View memory stats (for observing memory leak)
curl http://localhost:8000/debug/memory

# Clear caches
curl -X POST http://localhost:8000/debug/clear-caches
```

## Viewing Metrics

### Prometheus
1. Open http://localhost:9090
2. Example queries:
   - `product_cache_entries_total` - Cache size (memory leak indicator)
   - `payment_requests_total` - Payment success/failure counts
   - `http_request_duration_seconds_bucket` - Request latency

### Grafana
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to Dashboards > "Sentinel Bug Monitor"

The dashboard displays:
- **Memory Leak Detection**: Cache entries and memory usage over time
- **N+1 Query Issues**: /products endpoint latency percentiles
- **Payment Service Health**: Success rate, error rate, and latency
- **API Overview**: Request rates and status codes by endpoint

### Raw Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f payment-service

# Last 100 lines
docker-compose logs --tail=100 api
```

## Configuration

### Payment Service Failure Modes
Set the `FAILURE_MODE` environment variable on the payment-service:

```yaml
# In docker-compose.yml
payment-service:
  environment:
    - FAILURE_MODE=none        # Normal operation
    - FAILURE_MODE=rate_limit  # Returns 429 errors
    - FAILURE_MODE=timeout     # Slow responses
    - FAILURE_MODE=error       # Returns 500 errors
```

Restart after changes:
```bash
docker-compose up -d payment-service
```

## Triggering the Intentional Bugs

This application contains several intentional bugs for testing AI debugging capabilities.

---

### Bug 1: Memory Leak (Latency Spike)

The `/products` and `/product/:id` endpoints accumulate data in global caches that are never cleaned up. Each request adds entries to `_product_view_cache` (using timestamp-based keys) and `_product_analytics` list.

**How to trigger:**
```bash
# Make repeated requests to grow the caches
for i in {1..100}; do
  curl -s "http://localhost:8000/products" > /dev/null
  curl -s "http://localhost:8000/product/1" > /dev/null
done

# Check memory stats to see the leak
curl http://localhost:8000/products/debug/memory-stats

# Or via the debug endpoint
curl http://localhost:8000/debug/memory
```

**Symptoms:**
- `cache_entries` and `analytics_entries` grow without bound
- Response latency increases as memory fills (GC pressure)
- Memory usage climbs steadily over time
- Prometheus metric `product_cache_entries_total` keeps rising

**Prometheus queries:**
```
product_cache_entries_total
product_analytics_entries_total
estimated_leak_memory_bytes
```

**Reset the leak:**
```bash
curl -X POST http://localhost:8000/products/debug/clear-caches
```

---

### Bug 2: Slow LIKE Search (Full Table Scan)

The `/products` endpoint supports a `search` parameter that performs an inefficient
`LIKE '%term%'` query on non-indexed `name` and `description` columns.

**How to trigger:**
```bash
# Single request - noticeable latency with large datasets
curl "http://localhost:8000/products?search=electronics"

# Load test to see degradation
for i in {1..50}; do
  curl -s "http://localhost:8000/products?search=product$i" &
done
wait
```

**Symptoms:**
- Slow response times that worsen as product count grows
- High database CPU during searches
- `EXPLAIN ANALYZE` shows sequential scan instead of index scan

**Location:** `app/repositories/product_repository.py` - the `ilike()` filter

---

### Bug 3: In-Memory Filtering (min_price)

The `min_price` filter fetches ALL products from the database, then filters in Python
instead of using a SQL WHERE clause.

**How to trigger:**
```bash
# Request with min_price filter
curl "http://localhost:8000/products?min_price=100"

# Compare with max_price (which uses efficient SQL filtering)
curl "http://localhost:8000/products?max_price=100"

# Notice pagination inconsistency
curl "http://localhost:8000/products?min_price=50&page=1&page_size=5"
curl "http://localhost:8000/products?min_price=50&page=2&page_size=5"
```

**Symptoms:**
- Higher memory usage on API container
- Slower response than equivalent `max_price` filter
- Pagination returns inconsistent/incorrect totals
- Response time grows linearly with total product count (not page size)

**Location:** `app/repositories/product_repository.py` - in-memory list comprehension after query

---

### Bug 4: Third-Party Service Flake (Logic Error)

The `/checkout` endpoint calls an external payment service that can be configured to
return errors, timeouts, or rate limits. The API may not handle these failure modes gracefully.

**How to trigger:**

First, configure the payment service failure mode in `docker-compose.yml`:
```yaml
payment-service:
  environment:
    - FAILURE_MODE=rate_limit  # or: timeout, error, none
```

Then restart and test:
```bash
# Restart payment service with new failure mode
docker-compose up -d payment-service

# Make checkout requests
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 1}],
    "card_token": "tok_visa_123"
  }'

# Load test to trigger rate limiting
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/checkout \
    -H "Content-Type: application/json" \
    -d '{"items": [{"product_id": 1, "quantity": 1}], "card_token": "tok_visa"}' &
done
wait
```

**Failure modes:**
| Mode | Behavior |
|------|----------|
| `none` | Normal operation |
| `rate_limit` | Returns 429 Too Many Requests |
| `timeout` | Slow responses (simulated latency) |
| `error` | Returns 500 Internal Server Error |

**Symptoms:**
- 500 errors when payment service returns unexpected responses
- Missing error handling for rate limits (429)
- No circuit breaker pattern implemented
- Crashes when parsing malformed JSON responses

**Prometheus queries:**
```
payment_requests_total{status="success"}
payment_requests_total{status="failure"}
```
