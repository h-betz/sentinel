## What
API that mimics an e-commerce website

## Scenarios

### The "Memory Leaker" (Latency Spike)
Instead of a simple sleep(), create a function that progressively consumes memory or builds a massive list in a global variable every time it's called.

**The Fail:** As memory fills up, the Python Garbage Collector struggles, causing the API response time to climb from 50ms to 5,000ms.

**The AI's Job:** It shouldn't just "restart the server." It should look at the code, identify the global variable that's growing, and refactor it into a proper cache or database query.

### The "N+1 Deadlock" (500 Error)
Create a database endpoint that tries to perform a nested loop of queries without proper eager loading.

**The Fail:** Under "heavy load" (which you can simulate with a script), the database connection pool exhausts, and the API throws a TimeoutError or ConnectionError.

**The AI's Job:** The agent must identify that the database isn't "down"—it's being strangled by inefficient code. The fix is to implement joinedload or selectinload.

**IMPLEMENTED:** Two performance bugs have been added to replace the N+1 lazy loading bug:

1. **LIKE Search Bug** - The `search` query parameter performs `LIKE '%term%'` searches on non-indexed `name` and `description` columns, causing full table scans.

2. **In-Memory Filtering Bug** - The `min_price` filter fetches ALL products from the database, then filters in Python instead of using SQL WHERE clauses. This breaks pagination and causes O(n) memory usage.

### The "Third-Party Flake" (Logic Error)
Have your API call a "mock" payment gateway or shipping service that starts returning malformed JSON or a 429 Too Many Requests.

**The Fail:** Your API crashes because it's trying to parse response.json()['id'] but the key id is missing from the error response.

**The AI's Job:** It needs to implement a Circuit Breaker pattern or add robust "Try-Except" blocks with fallback logic.

## Endpoints
`GET /products` - returns a list of products, 50 max at a time. Should support filtering. Pulls data from DB

`GET /product/:id` - returns more detailed information on a product from the DB

`POST /checkout` -  calls an internal payment service (more on that below)
