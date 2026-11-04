# PROTOCOL.md: Urja Meter Ops Upstream Portal Investigation Report

## 1. Application Overview

- **Host / URL**: `https://urja-ops.flockenergy.tech`
- **Application Framework**: SvelteKit (`x-sveltekit-page: true`) with TailwindCSS.
- **Frontend Architecture**: Client-side hydrated SPA powered by Svelte 5 / SvelteKit client runtime (`_app/immutable/entry/start.*.js`, `_app/immutable/entry/app.*.js`).
- **Core Domain**: Distribution metering operations portal for electricity distribution grids in India (specifically Jaipur DISCOM context, with hierarchy ranging from Zone down to Distribution Transformer).
- **Portal Modules Identified**:
  1. `/login`: Authentication gate with email and password form.
  2. `/meters`: Primary meter inventory table, search, and pagination.
  3. `/meters/[id]`: Individual meter nameplate, location (lat/long), hierarchy breadcrumbs, and consumption/voltage history table.
  4. `/transformers`: Distribution Transformers (DT) directory with pagination and HMAC-signed bulk meter export trigger.

---

## 2. Authentication Mechanism

- **Auth Framework**: `Better Auth` (`__Secure-better-auth.session_token` cookie).
- **Login Endpoint**: `POST https://urja-ops.flockenergy.tech/login`
- **Required Upstream Headers for Login**:
  - `Content-Type: application/x-www-form-urlencoded`
  - `Accept: application/json`
  - `x-sveltekit-action: true`
  - `Origin: https://urja-ops.flockenergy.tech` (Mandatory; without this header SvelteKit returns `403 Forbidden` due to CSRF protection)
  - `Referer: https://urja-ops.flockenergy.tech/login`
- **Payload Format**: `email={email}&password={password}` (URL-encoded form data)
- **Login Response**:
  - HTTP Status: `200 OK`
  - Body: `{"type": "redirect", "status": 303, "location": "/meters"}`
  - Cookie Set: `__Secure-better-auth.session_token=<token>; Max-Age=3600; Path=/; HttpOnly; Secure; SameSite=Lax`
- **Session Lifespan**: `Max-Age=3600` (1 hour / 3600 seconds).
- **Session Validation & Re-authentication**:
  - When the session expires or is missing, requesting protected endpoints or navigating to `/` or `/meters` responds with a redirect (`302`/`303` to `/login`) or `401 Unauthorized`.
  - The client adapter must detect 401/303 responses, execute automatic re-authentication using stored credentials, and retry the failed request with the new cookie.

---

## 3. Discovered Data Resources and Endpoints

### 3.1 Meter Search / Listing
- **Endpoint**: `GET /portal/meters/search?q={query}&page={page}`
- **Parameters**:
  - `q` (string, optional): Search query matching `meterId` or `serialNo`.
  - `page` (integer, 1-indexed, default `1`): Page number.
- **Upstream Response Structure**:
  ```json
  {
    "data": [
      {
        "meterId": "J100000",
        "serialNo": "SE33962",
        "make": "HPL",
        "phaseType": "single",
        "installStatus": "Decommissioned",
        "dtCode": "DT-001"
      }
    ],
    "total": 403
  }
  ```
- **Page Size**: Fixed at 20 items per page (21 total pages for 403 items).

### 3.2 Meter Details & Hierarchy
- **Endpoint 1 (Page Data)**: `GET /meters/{meterId}/__data.json`
  - Returns SvelteKit devalue serialized nodes containing user session, meter detail parameters (`data` array with `parameterName`/`parameterValue` or `classData`), and electrical hierarchy.
- **Hierarchy Structure**:
  - `Zone`: e.g., `"Jaipur Zone 1 (Z-01)"`
  - `Circle`: e.g., `"Circle 1 (C-01)"`
  - `Division`: e.g., `"Division 1 (D-01)"`
  - `Subdivision`: e.g., `"Subdivision 1 (SD-01)"`
  - `Sub Station`: e.g., `"Substation 1 (SS-01)"`
  - `Feeder`: e.g., `"Feeder 1 (F-001)"`
  - `DT`: e.g., `"Malviya Nagar DT 1 (DT-001)"`

### 3.3 Meter Geolocation
- **Endpoint**: `GET /portal/meters/{meterId}/geo`
- **Response**:
  ```json
  {
    "data": {
      "latitude": "26.938961002479868",
      "longitude": "75.83095696146852"
    }
  }
  ```
- **Data Types**: Note that the upstream endpoint returns latitude and longitude as *strings* instead of native floats. Our API normalizes them to IEEE 754 floats.

### 3.4 Meter Energy & Consumption Readings
- **Endpoint**: `GET /portal/meters/{meterId}/energy`
- **Response**:
  ```json
  {
    "data": [
      {
        "timestamp": "23/06/2026 23:30",
        "kwh": "48438.74",
        "kvah": "52313.84",
        "voltR": "226"
      }
    ]
  }
  ```
- **Data Types & Interval**:
  - `timestamp`: String in Indian local format `DD/MM/YYYY HH:MM`.
  - `kwh`: String representation of cumulative active energy in kiloWatt-hours.
  - `kvah`: String representation of cumulative apparent energy in kiloVolt-Ampere-hours.
  - `voltR`: String representation of phase R voltage in Volts.
  - Interval: 30-minute interval profile data or daily snapshots (8 to 337 readings).

### 3.5 Distribution Transformers (DTs)
- **Endpoint**: `GET /portal/dts?page={page}`
- **Parameters**: `page` (1-indexed). Total count is 40 across 2 pages (20 per page).
- **Response**:
  ```json
  {
    "data": [
      {
        "code": "DT-001",
        "name": "Malviya Nagar DT 1",
        "feederCode": "F-001",
        "capacityKva": 100
      }
    ],
    "total": 40
  }
  ```

### 3.6 HMAC-SHA256 Signed Bulk Meter Export
- **Key Retrieval**: `GET /portal/keys`
  - Response: `{"data": {"signingSecret": "..."}}`
- **Export Endpoint**: `GET /portal/export?page=1`
- **Signing Algorithm**: HMAC-SHA256
  - Message Format: `[METHOD]\n[PATH]\n[QUERY]\n[TIMESTAMP]`
  - Example: `"GET\n/portal/export\npage=1\n1730712000"`
  - Headers:
    - `x-timestamp`: Unix epoch seconds string
    - `x-signature`: 64-character lowercase hex HMAC-SHA256 digest
- **Export Response**:
  - Contains **all 403 meters in a single API call**, fully enriched with:
    - `meterId`
    - `serialNo`
    - `make`
    - `phaseType`
    - `installStatus`
    - `installType`
    - `build`
    - `dtCode`
    - `hierarchy` (parsed dictionary with structured name and code for zone, circle, division, subdivision, substation, feeder, dt)
    - `geo` (`{"lat": 26.9389..., "lng": 75.8309...}`)

---

## 4. Dataset Inventory & Empirical Statistics

An empirical census of the entire upstream dataset (all 403 meters and 40 DTs) revealed:

| Attribute | Observed Values & Distribution |
| :--- | :--- |
| **Total Meters** | 403 meters |
| **Total Transformers** | 40 Distribution Transformers |
| **Makes** | `HPL` (90), `Genus` (88), `Secure` (85), `Allied` (76), `L&T` (64) |
| **Phase Types** | `single` (277, ~68.7%), `three` (126, ~31.3%) |
| **Installation Statuses**| `Installed` (238, ~59.1%), `Faulty` (90, ~22.3%), `Decommissioned` (75, ~18.6%) |
| **Installation Types** | `Whole Current` (205), `CT Operated` (198) |
| **Firmware / Build** | `legacy` (238), `v2` (165) |
| **Orphaned DT Codes** | `0` (100% of meter DT codes map to valid DTs in `/portal/dts`) |
| **Missing Coordinates**| `0` (All 403 meters have valid GPS latitude and longitude) |
| **Hierarchy Gaps** | `0` (All 403 meters have complete 7-level electrical hierarchies) |

---

## 5. Architectural Implications & Ingestion Strategy

1. **High Performance Synchronization**:
   Rather than performing $403 \times 3 = 1209$ slow, rate-limit-prone requests to fetch individual meter detail and geo endpoints, the service leverages the upstream HMAC-signed bulk `/portal/export` endpoint.
2. **In-Memory Query Layer with TTL**:
   An in-memory local cache/repository caches the normalized inventory of all 403 meters and 40 transformers with a configurable TTL (default: 300s). This provides sub-millisecond response times for complex filtering (by `make`, `phase_type`, `status`, `dt_code`, `feeder_code`, full-text `search`, sorting, and pagination) without putting load on the upstream portal.
3. **On-Demand Interval Reading Fetch**:
   Energy readings (`/portal/meters/{id}/energy`) are fetched on-demand and cached per meter with a short TTL (120s), ensuring real-time freshness while preventing duplicate upstream calls.
4. **Data Normalization**:
   - Dates: String timestamps (`DD/MM/YYYY HH:MM`) are normalized to standard ISO-8601 UTC timestamps (`YYYY-MM-DDTHH:MM:SSZ`).
   - Floats: String quantities (`kwh`, `kvah`, `voltR`, `latitude`, `longitude`) are safely parsed and validated into native numerical types.
   - Response Envelope: Consistent `{ success: true, data: ..., meta: ... }` contract across all endpoints.
