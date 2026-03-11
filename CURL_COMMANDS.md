# toy_app API — curl Commands

Base URL: `http://localhost:8000`

---

## Health Check

```bash
curl http://localhost:8000/health
```

---

## Products

### List products (default)
```bash
curl http://localhost:8000/products
```

### Paginate
```bash
curl "http://localhost:8000/products?page=2&page_size=10"
```

### Filter by category
```bash
curl "http://localhost:8000/products?category_id=1"
```

### Filter by price range
```bash
curl "http://localhost:8000/products?min_price=10&max_price=100"
```

### In-stock only
```bash
curl "http://localhost:8000/products?in_stock=true"
```

### Search (triggers the LIKE bug — slow on large datasets)
```bash
curl "http://localhost:8000/products?search=widget"
```

### Combined filters (triggers in-memory filtering bug)
```bash
curl "http://localhost:8000/products?min_price=20&in_stock=true&search=widget"
```

### Get single product
```bash
curl http://localhost:8000/product/1
```

---

## Checkout (triggers the payment flake bug)

### Basic checkout
```bash
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "customer_name": "Test User",
    "card_token": "tok_test_123",
    "items": [
      { "product_id": 1, "quantity": 2 }
    ]
  }'
```

### Multi-item checkout
```bash
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "customer_name": "Test User",
    "card_token": "tok_test_123",
    "items": [
      { "product_id": 1, "quantity": 1 },
      { "product_id": 2, "quantity": 3 },
      { "product_id": 5, "quantity": 1 }
    ]
  }'
```

---

## Debug Endpoints

### Observe the memory leak (watch cache entries grow)
```bash
curl http://localhost:8000/products/debug/memory-stats
```

### Reset the memory leak counters
```bash
curl -X POST http://localhost:8000/products/debug/clear-caches
```

---

## Stress Testing

Hammer `/products` to grow the memory leak:
```bash
for i in $(seq 1 50); do curl -s http://localhost:8000/products?search=test > /dev/null; done
```

Hammer `/checkout` to trigger payment flake errors:
```bash
for i in $(seq 1 30); do
  curl -s -X POST http://localhost:8000/checkout \
    -H "Content-Type: application/json" \
    -d '{"customer_email":"test@example.com","customer_name":"Test User","card_token":"tok_test_123","items":[{"product_id":1,"quantity":1}]}' \
    > /dev/null
done
```
