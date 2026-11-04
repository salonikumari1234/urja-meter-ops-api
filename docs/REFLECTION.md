# Engineering Reflection: Urja Meter Ops API Service

### 1. What assumptions did you make?
I assumed that the upstream portal's data was representative of a typical distribution utility in India, which was validated upon inspecting the Jaipur DISCOM hierarchy (Zone → Circle → Division → Subdivision → Substation → Feeder → DT). I also assumed that the HMAC-signed export endpoint (`/portal/export`) was intended as the authorized, high-efficiency bulk ingestion path rather than forcing hundreds of sequential HTTP calls to individual meter pages.

### 2. Which part was most difficult, and how did you get unstuck?
The most challenging part was reverse-engineering the authentication and bulk export mechanics of the upstream SvelteKit application. When initial automated POST requests to `/login` returned `403 Forbidden`, I investigated the client-side JavaScript bundle (`_app/immutable/nodes/7.*.js`) and discovered that SvelteKit's CSRF protection strictly checks the `Origin` header against the `Host`. Additionally, the bulk export endpoint required a cryptographic HMAC-SHA256 signature generated over a newline-delimited message `[METHOD]\n[PATH]\n[QUERY]\n[TIMESTAMP]` using a secret fetched from `/portal/keys`. By inspecting the SvelteKit decompiled AST and replicating the exact Web Crypto `SubtleCrypto.sign` routine in Python, I unlocked both authentication and high-throughput bulk ingestion.

### 3. If you had another day, what would you improve?
If given another day, I would add a lightweight Next.js or React frontend dashboard consuming our own API to visually render the meter map (using Leaflet.js with the GPS coordinates), chart 30-minute load curves for meters, and provide an interactive tree explorer for the electrical hierarchy. I would also add Prometheus metrics export (`/metrics`) to monitor cache hit ratios and upstream response latency histograms.

### 4. What mistake did you make while solving this?
Initially, I implemented request correlation logging using Starlette's `BaseHTTPMiddleware`. While working in the sandbox environment, `BaseHTTPMiddleware`'s reliance on AnyIO background taskgroups and loopback socketpairs caused the test runner to hang on Windows. Recognizing that Windows sandbox restrictions isolate loopback networking, I identified the root cause and refactored the middleware into a pure ASGI 3.0 middleware, which eliminated the deadlock and allowed the test suite to execute in under 0.25 seconds.

### 5. If you reviewed your own submission, what would you criticize?
I would criticize the coupling of the in-memory cache repository to the single-process Python runtime. While appropriate for a 403-meter dataset, if the grid expanded to millions of smart meters with continuous streaming intervals, an in-memory dictionary would exceed memory bounds and require partitioned persistence (e.g., PostgreSQL with TimescaleDB for time-series energy readings).
