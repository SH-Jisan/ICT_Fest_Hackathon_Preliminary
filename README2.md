# CoWork API — Technical Documentation & Code Review

This document serves as the comprehensive technical documentation and code review report for the **CoWork API**, a multi-tenant coworking space booking system. It outlines the project's architecture, directory structure, module responsibilities, database schema, data flow, technical debt, and a detailed code review identifying critical bugs and vulnerabilities along with their recommended solutions.

---

## 1. Project Overview & Purpose

**CoWork** is a multi-tenant REST API built to manage room bookings within shared coworking spaces. The system supports multiple independent organizations (tenants), each having its own isolated set of rooms, members, and administrators. 

### Key Capabilities:
- **Multi-Tenancy**: Data isolation across organizations. Users and admins can only access and modify resources within their own tenant scope.
- **Role-Based Access Control (RBAC)**: Distinguishes between **Admins** (who manage rooms, view usage reports, and export booking history) and **Members** (who book rooms and manage their own bookings).
- **Booking Rules Validation**: Enforces duration limits, quota restrictions (max 3 bookings in a 24-hour window), and overlap prevention (no double-booking of rooms).
- **Token-based Authentication**: JWT-based authentication system featuring access and refresh token rotation, logout revocation, and single-use refresh tokens.
- **Reporting and Data Export**: Provides live room statistics, usage reports for date ranges, and CSV data exports.

---

## 2. System Architecture & Design Patterns

The CoWork API is structured as a monolithic layered backend using the **FastAPI** framework:

```
┌────────────────────────────────────────────────────────┐
│                      Client / API                      │
└───────────────────────────┬────────────────────────────┘
                            │ (HTTP Requests)
┌───────────────────────────▼────────────────────────────┐
│                  Routers (Controllers)                 │
│              (auth.py, rooms.py, bookings.py, ...)     │
└───────────────────────────┬────────────────────────────┘
                            │ (Validates Schemas & Calls)
┌───────────────────────────▼────────────────────────────┐
│                    Service Layer                       │
│        (stats.py, ratelimit.py, refunds.py, ...)       │
└───────────────────────────┬────────────────────────────┘
                            │ (Interacts with DB & Models)
┌───────────────────────────▼────────────────────────────┐
│                  Database & ORM Model                  │
│                     (SQLAlchemy ORM)                   │
└────────────────────────────────────────────────────────┘
```

### Design Patterns Used:
1. **Dependency Injection (DI)**: FastAPI's `Depends` is heavily used to inject request-scoped database sessions (`get_db`), parse token payloads (`get_token_payload`), retrieve current authenticated users (`get_current_user`), and enforce admin authorization (`require_admin`).
2. **Repository/Active Record**: SQLAlchemy ORM models act as representations of database tables. Database interactions are handled inside routers and services using SQLAlchemy query builders.
3. **Pydantic Schemas**: Separate schemas define request payloads (data validation and sanitization) and serialize response payloads.
4. **Thread-Lock Synchronization**: Global `threading.Lock` instances are used in side-effect services (such as auditing and notifications) to simulate synchronized sequential execution.
5. **In-Memory Caching**: Cache structures (`dict`) hold computed results for reports and room availabilities, which are programmatically invalidated upon database modifications.

---

## 3. Directory & Folder Structure

```
d:\ICT_Fest_Hackathon_Preliminary\
├── app/                      # Core application source code
│   ├── routers/              # API Endpoint definitions (Controllers)
│   ├── services/             # Domain business logic & background services
│   ├── __init__.py           # Package marker
│   ├── auth.py               # Authentication helper functions & dependencies
│   ├── cache.py              # In-memory caching mechanisms
│   ├── config.py             # Environment configuration loading
│   ├── database.py           # SQLAlchemy setup & session management
│   ├── errors.py             # Custom application exception handlers
│   ├── main.py               # FastAPI application entrypoint
│   ├── models.py             # SQLAlchemy ORM schemas (entities)
│   ├── schemas.py            # Pydantic validation schemas
│   └── serializers.py        # Entity-to-dictionary serialization helpers
├── manual/                   # Documentation and compiled manuals
│   ├── assets/               # Image assets used in the PDF manual
│   └── ...
├── tests/                    # Test suites
│   ├── __init__.py           # Package marker
│   └── test_smoke.py         # End-to-end happy-path integration test
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker compose services mapping
├── requirements.txt          # Python dependency list
└── README2.md                # Comprehensive technical documentation (this file)
```

---

## 4. File-by-File Responsibility Matrix

| File Path | Description / Responsibility |
| :--- | :--- |
| `app/main.py` | Initializes the FastAPI app, registers routes, sets up global database schema creation (`metadata.create_all`), and attaches custom exception handlers. |
| `app/config.py` | Reads environment variables (`JWT_SECRET`, `DATABASE_URL`) and defines application-wide default constants. |
| `app/database.py` | Configures the SQLAlchemy database engine (using SQLite as a backend) and yields request-scoped database sessions via `get_db`. |
| `app/models.py` | Declares all database schemas (`Organization`, `User`, `Room`, `Booking`, `RefundLog`) and sets up relationships. |
| `app/schemas.py` | Houses Pydantic models for incoming data structures, ensuring basic type safety and validation (e.g. `RegisterRequest`, `BookingCreateRequest`). |
| `app/serializers.py` | Provides helper functions like `serialize_booking` to convert ORM instances into dictionaries that conform to the API's contract. |
| `app/auth.py` | Handles password hashing (PBKDF2-SHA256), JWT token generation, parsing, validation, token revocation, and FastAPI authentication dependencies. |
| `app/cache.py` | Implements in-memory caches (`_report_cache` and `_availability_cache`) to speed up heavy reporting queries. |
| `app/errors.py` | Defines `AppError` and registers custom exception handlers to format validation/business rule failures into consistent API error JSONs. |
| `app/timeutils.py` | Provides utility functions for ISO 8601 parsing, converting datetime inputs, and outputting explicit UTC strings. |
| `app/routers/health.py` | Contains the `/health` endpoint to verify service liveness. |
| `app/routers/auth.py` | Exposes auth paths (`/register`, `/login`, `/refresh`, `/logout`). |
| `app/routers/rooms.py` | Defines endpoints to list/create rooms, fetch date-specific availabilities, and retrieve room stats. |
| `app/routers/bookings.py` | Handles creation, listing, cancellation, and retrieval of room bookings. |
| `app/routers/admin.py` | Exposes administrative routes (`/usage-report` and `/export` CSV dump). |
| `app/services/ratelimit.py` | Contains a rolling-window in-memory request tracker to limit booking creations per user to 20 requests/minute. |
| `app/services/reference.py` | Issues unique sequential human-friendly reference codes (e.g., `CW-001042`) using an in-memory counter. |
| `app/services/stats.py` | Tracks incremental per-room booking statistics (booking count, total revenue) in memory. |
| `app/services/refunds.py` | Calculates and logs refunds into `refund_logs` when a booking is cancelled. |
| `app/services/notifications.py`| Simulates emails and appends logs on booking creations and cancellations using thread locks. |
| `app/services/export.py` | Generates formatted CSV outputs of bookings scoped by organization, user, and room. |

---

## 5. System Data Flow Workflows

### A. User Registration & Login Flow
1. **Client** calls `POST /auth/register` with `org_name`, `username`, and `password`.
2. **Router** queries if `org_name` exists. If not, it creates a new `Organization` and assigns the registering user as the `admin` (subsequent users joining an existing organization are assigned the `member` role).
3. The password is hashed using PBKDF2 with 100,000 rounds and stored.
4. **Client** calls `POST /auth/login` and receives an `access_token` (expires in 15 mins) and a `refresh_token` (expires in 7 days).

### B. Room Booking Creation Flow

```
Client         Rate Limit        Database Check       Quota Audit        Stats & Cache      Client
  │                │                   │                  │                    │              │
  ├─(POST Booking)─┼───────────────────┼──────────────────┼────────────────────┼─────────────>│
  │                ├─(Check Limits)    │                  │                    │              │
  │                │   [100ms delay]   │                  │                    │              │
  │                └─────────┬────────>│                  │                    │              │
  │                          ├─(Conflict Check)           │                    │              │
  │                          │  [120ms delay]             │                    │              │
  │                          └─────────┬─────────────────>│                    │              │
  │                                    ├─(Quota check)    │                    │              │
  │                                    │  [100ms delay]   │                    │              │
  │                                    └────────┬────────>│                    │              │
  │                                             ├─(Save Booking)               │              │
  │                                             └─────────┬───────────────────>│              │
  │                                                       ├─(Increment Stats)  │              │
  │                                                       ├─(Invalidate Cache) │              │
  │                                                       └────────┬───────────┼─────────────>│
  │                                                                │           │              │
  │<───────────────────────────────────(201 Created Response)──────┴───────────┘              │
```

### C. Booking Cancellation Flow
1. **Client** sends `POST /bookings/{id}/cancel`.
2. **Router** verifies the booking belongs to the caller's organization.
3. Enforces authorization (owner of booking or organization admin).
4. Calculates the refund notice interval: `notice = start_time - now`.
5. Logs a `RefundLog` record in the database.
6. Updates booking status to `cancelled`.
7. Updates room stats, clears organization usage reports cache, and triggers a cancellation email.

---

## 6. Database Schema & Relationships

The SQLite database is managed through SQLAlchemy. The tables and columns are defined as follows:

```
  ┌──────────────────┐          ┌──────────────────────┐          ┌──────────────────┐
  │  organizations   │          │        users         │          │      rooms       │
  ├──────────────────┤          ├──────────────────────┤          ├──────────────────┤
  │ PK id (INT)      │◄──┐      │ PK id (INT)          │◄──┐      │ PK id (INT)      │◄──┐
  │    name (STR)    │   │      │ FK org_id (INT)      │   │      │ FK org_id (INT)  │   │
  └──────────────────┘   │      │    username (STR)    │   │      │    name (STR)    │   │
                         │      │    hashed_pwd (STR)  │   │      │    capacity (INT)│   │
                         │      │    role (STR)        │   │      │    rate_cents(INT)   │
                         │      │    created_at (DT)   │   │      └──────────────────┘   │
                         │      └──────────────────────┘   │                             │
                         │                                 │                             │
                         │                                 │                             │
                         └─────────────────────────────────┼─────────────────────────────┤
                                                           │                             │
                                                ┌──────────┴──────────┐                  │
                                                │      bookings       │                  │
                                                ├─────────────────────┤                  │
                                                │ PK id (INT)         │                  │
                                                │ FK room_id (INT)────┼──────────────────┘
                                                │ FK user_id (INT)    │
                                                │    start_time (DT)  │
                                                │    end_time (DT)    │
                                                │    status (STR)     │
                                                │    ref_code (STR)   │
                                                │    price_cents (INT)│
                                                │    created_at (DT)  │
                                                └──────────┬──────────┘
                                                           │
                                                           │ (1 to many)
                                                           ▼
                                                ┌─────────────────────┐
                                                │    refund_logs      │
                                                ├─────────────────────┤
                                                │ PK id (INT)         │
                                                │ FK booking_id (INT) │
                                                │    amount_cents(INT)│
                                                │    status (STR)     │
                                                │    processed_at (DT)│
                                                └─────────────────────┘
```

---

## 7. Authentication & Authorization Flow

### JWT Token Claims
Every generated JWT contains the following claims:
- `sub`: User ID (cast as a string).
- `org`: Organization ID (integer).
- `role`: Role of the user (`admin` or `member`).
- `jti`: Unique token identifier (UUID hex).
- `iat`: Epoch timestamp when token was issued.
- `exp`: Expiration epoch timestamp.
- `type`: Token type (`access` or `refresh`).

### Token Revocation List
Revoked tokens are stored in an in-memory set `_revoked_tokens`. When a user logs out (`POST /auth/logout`), the token's identifier is appended to the set, blocking further requests that present that specific token.

### Authorization Check
- **`get_current_user`**: Resolves the bearer token in the `Authorization` header, decodes the JWT, checks that it is an access token, confirms it is not revoked, and queries the user from the database.
- **`require_admin`**: Depends on `get_current_user` and asserts that `user.role == "admin"`. If false, raises a `403 FORBIDDEN` error.

---

## 8. API Endpoint Documentation

| Method | Path | Auth | Success Code | Error Codes | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | No | 201 | 409 | Registers a new user. The first user of an organization becomes `admin`; subsequent ones are `member`. |
| **POST** | `/auth/login` | No | 200 | 401 | Authenticates credentials and returns access + refresh tokens. |
| **POST** | `/auth/refresh` | No | 200 | 401 | Decodes a valid refresh token, invalidates it, and returns a new token pair. |
| **POST** | `/auth/logout` | Yes | 200 | 401 | Revokes the current access token. |
| **GET** | `/rooms` | Yes | 200 | 401 | Lists all rooms within the user's organization. |
| **POST** | `/rooms` | Yes | 201 | 401, 403 | Creates a room (Admin-only). |
| **GET** | `/rooms/{id}/availability` | Yes | 200 | 400, 401, 404 | Lists busy intervals for a room on a specific date (`YYYY-MM-DD`). |
| **GET** | `/rooms/{id}/stats` | Yes | 200 | 401, 404 | Returns room booking metrics (Admin-only). |
| **POST** | `/bookings` | Yes | 201 | 400, 401, 409, 429 | Creates a room booking. Validates limits and conflicts. |
| **GET** | `/bookings` | Yes | 200 | 401 | Lists the user's own bookings (paginated, sorted). |
| **GET** | `/bookings/{id}` | Yes | 200 | 401, 404 | Retrieves booking details (scoped by tenant and visibility rules). |
| **POST** | `/bookings/{id}/cancel` | Yes | 200 | 401, 404, 409 | Cancels a booking and registers refunds. |
| **GET** | `/admin/usage-report` | Yes | 200 | 400, 401, 403 | Returns room usage reports for a range (Admin-only). |
| **GET** | `/admin/export` | Yes | 200 | 401, 403, 404 | Exports booking ledger as a CSV file (Admin-only). |
| **GET** | `/health` | No | 200 | None | Verification endpoint for service health. |

---

## 9. Environment Variables & Third-Party Libraries

### Environment Variables
- `JWT_SECRET`: Secret key used for signing HS256 JWT tokens. Defaults to `cowork-dev-secret-change-me` in development.
- `DATABASE_URL`: SQLAlchemy-compatible database connection string. Defaults to `sqlite:///./cowork.db` (local development) and overridden to `sqlite:////app/data/cowork.db` in Docker environments to persist data on a Docker volume.

### Dependencies Matrix
- `fastapi` (0.111.0): Backend web framework for building APIs.
- `uvicorn[standard]` (0.30.1): ASGI server to serve the FastAPI app.
- `SQLAlchemy` (2.0.30): SQL toolkit and Object-Relational Mapper (ORM).
- `pydantic` (2.7.1): Data validation and settings management using Python type annotations.
- `PyJWT` (2.8.0): Python library to encode and decode JSON Web Tokens.

---

## 10. Core Assumptions, Limitations, & Technical Debt

1. **SQLite Database Limitations**: SQLite is a file-based database. It lacks support for native row-level write locks (`FOR UPDATE`), making concurrency control difficult and exposing the system to race conditions unless serialized write modes or external synchronization are used.
2. **State Volatility (Memory Loss on Restart)**: The following critical components are stored purely in-memory:
   - **Revoked access/refresh tokens**: Lost on restart, allowing blacklisted tokens to become valid again.
   - **User Rate-Limit buckets**: Reset on restart.
   - **Room Statistics cache (`_stats`)**: Reset on restart, returning `{"count": 0, "revenue": 0}` regardless of actual database bookings.
   - **Reference code counter**: Resets on restart, potentially causing duplicates if not carefully handled.
3. **Database Migration Deficit**: The codebase lacks database migration setup (such as Alembic). Database structure modifications require manually dropping tables, which is dangerous for production deployments.
4. **Artificial Latency Bottlenecks**: The code contains artificial delay calls (`time.sleep(0.1)` to `time.sleep(0.12)`) in rate limiting, conflict checking, reference code generation, and cancellation. These slow down execution, reducing performance and increasing the duration of transactions, which worsens concurrency race windows.

---

## 11. Code Review, Bugs, & Security Vulnerabilities Report

This section outlines all bugs, logic errors, and security issues identified in the codebase, categorized by severity.

### Summary Table of Issues

| # | File Path | Line(s) | Severity | Description |
|---|---|---|---|---|
| 1 | `app/timeutils.py` | 11-14 | **High** | Incorrect DateTime timezone normalization (strips offset without converting). |
| 2 | `app/auth.py` | 85-86, 97-98 | **Critical** | Broken Token Revocation check (compares JTI to User ID). |
| 3 | `app/routers/auth.py` | 37-43 | **High** | Returns 200 OK instead of 409 USERNAME_TAKEN during duplicate user registrations. |
| 4 | `app/routers/auth.py` | 81-93 | **Critical** | Missing Refresh Token invalidation and reuse check. |
| 5 | `app/routers/bookings.py` | 89-94 | **Critical** | Zero or Negative booking durations permitted. |
| 6 | `app/routers/bookings.py` | 86-87 | **High** | 5-minute past booking grace window violates "strict future" requirement. |
| 7 | `app/routers/bookings.py` | 137-139 | **High** | Broken bookings list pagination offset, hardcoded limits, and inverted sorting. |
| 8 | `app/routers/bookings.py` | 166 | **High** | Overwrites `start_time` with creation time in booking detail endpoint. |
| 9 | `app/routers/bookings.py` | 199-206 | **High** | Incorrect cancellation notice threshold calculations and 50% refund fallback bug. |
| 10 | Multiple files | Multiple | **High** | Mismatch in rounding/truncation logic of refund cents between routes and ledger services. |
| 11 | `app/services/notifications.py` | 24-36 | **Critical** | Nested lock acquisition deadlock between creation and cancellation calls. |
| 12 | `app/services/reference.py` | 17-21 | **Critical** | Race condition in reference code generation (non-thread-safe counter with 120ms sleep). |
| 13 | `app/services/stats.py` | 15-26 | **Critical** | Race condition in stats updates and loss of persistence on restart. |
| 14 | `app/services/export.py` | 22-29, 48-50 | **Critical** | Security Bypass: Scopeless room bookings export leaks data across organizations. |
| 15 | `app/routers/bookings.py` | 216-218 | **High** | Missing invalidation of room availability cache on cancellation. |
| 16 | `app/routers/bookings.py` | 119-122 | **Medium** | Missing invalidation of organization usage report cache on booking creation. |
| 17 | `app/routers/rooms.py` | 80-90 | **High** | Incomplete availability fetch fails to detect bookings overlapping across dates. |
| 18 | `app/auth.py` | 106 | **Medium** | Potential crash (500) if sub is not a valid integer. |

---

### Detailed Analysis of Issues

### 1. Incorrect DateTime Timezone Normalization
* **File Path**: `app/timeutils.py`
* **Line Number(s)**: 11-14
* **Severity**: **High**
* **Problem**: The parser strips the timezone offset (`tzinfo = None`) from the datetime object without converting it to UTC first.
* **Impact**: If a client sends `2026-07-09T18:00:00+06:00` (which is `12:00:00` UTC), the system strips the offset and stores it as `18:00:00` UTC. This causes bookings to be recorded at the wrong time, corrupting overlap checks and quota windows.
* **Recommended Solution**: Convert the datetime to UTC using `.astimezone(timezone.utc)` before stripping the timezone info.
* **Example Fix**:
```python
def parse_input_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
```

---

### 2. Broken Token Revocation Check
* **File Path**: `app/auth.py`
* **Line Number(s)**: 85-86, 97-98
* **Severity**: **Critical**
* **Problem**: The system registers a revoked token's `jti` claim (a UUID string) into `_revoked_tokens`. However, the token validator checks if the user's ID (`sub`) is in `_revoked_tokens`.
* **Impact**: Since a user's ID (e.g. `"1"`) will never match a token's `jti` UUID, revoked access tokens are never recognized as blacklisted. Users cannot log out effectively, exposing them to token replay attacks.
* **Recommended Solution**: Verify that the token's `jti` is in `_revoked_tokens`.
* **Example Fix**:
```python
# In app/auth.py
if payload.get("jti") in _revoked_tokens:
    raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
```

---

### 3. Missing 409 USERNAME_TAKEN during Registration
* **File Path**: `app/routers/auth.py`
* **Line Number(s)**: 37-43
* **Severity**: **High**
* **Problem**: If a registration request contains a username that already exists inside the target organization, the system returns the existing user's details with a `200 OK` status instead of raising a `409` conflict.
* **Impact**: Violates business rule 15 and allows anyone to check user membership details and enumerate usernames within an organization.
* **Recommended Solution**: Raise an `AppError` when a duplicate username is detected.
* **Example Fix**:
```python
if existing is not None:
    raise AppError(409, "USERNAME_TAKEN", "Username already taken within this organization")
```

---

### 4. Missing Refresh Token Invalidation & Reuse Check
* **File Path**: `app/routers/auth.py`
* **Line Number(s)**: 81-93
* **Severity**: **Critical**
* **Problem**: Refresh tokens are supposed to be single-use. However, the `/auth/refresh` route does not check if the refresh token is blacklisted, nor does it blacklist the token upon use.
* **Impact**: An attacker who obtains a refresh token can reuse it indefinitely to generate access tokens.
* **Recommended Solution**: Validate the refresh token's `jti` against the blacklist and blacklist it after it is refreshed.
* **Example Fix**:
```python
@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Wrong token type")
    if data.get("jti") in _revoked_tokens:
        raise AppError(401, "UNAUTHORIZED", "Token has been used or revoked")
    
    user = db.query(User).filter(User.id == int(data["sub"])).first()
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "Unknown user")
        
    revoke_access_token(data) # Blacklist the used refresh token
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "token_type": "bearer",
    }
```

---

### 5. Negative or Zero Booking Duration Allowed
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 89-94
* **Severity**: **Critical**
* **Problem**: The booking duration check validates that the duration is less than or equal to `MAX_DURATION_HOURS` (8) but fails to check the minimum limit `MIN_DURATION_HOURS` (1).
* **Impact**: Users can book rooms for negative durations (e.g. `end_time` before `start_time`). This results in negative pricing (`price_cents` will be negative) and bypasses conflicts.
* **Recommended Solution**: Validate that the booking duration is between 1 and 8 hours.
* **Example Fix**:
```python
duration_hours = (end - start).total_seconds() / 3600
if duration_hours != int(duration_hours):
    raise AppError(400, "INVALID_BOOKING_WINDOW", "duration must be a whole number of hours")
duration_hours = int(duration_hours)
if not (1 <= duration_hours <= 8):
    raise AppError(400, "INVALID_BOOKING_WINDOW", "duration out of range (must be 1-8 hours)")
```

---

### 6. Booking Past Grace Window Allowed
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 86-87
* **Severity**: **High**
* **Problem**: The system subtracts 5 minutes (`300` seconds) from the current time when validating if the booking starts in the future.
* **Impact**: Violates business rule 2 ("no grace window of any size"), allowing bookings to start up to 5 minutes in the past.
* **Recommended Solution**: Change the comparison so that `start_time` must be strictly after `now`.
* **Example Fix**:
```python
if start <= now:
    raise AppError(400, "INVALID_BOOKING_WINDOW", "start_time must be in the future")
```

---

### 7. Broken Bookings Pagination, Limit, and Sorting
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 137-139
* **Severity**: **High**
* **Problem**:
  1. The pagination query uses `offset(page * limit)`. For page 1, this offsets by 10, skipping the first page of results.
  2. The page limit is hardcoded to `.limit(10)`, ignoring the client-supplied query parameter.
  3. The sort order uses `Booking.start_time.desc()`, which is descending.
* **Impact**: Violates business rule 11. Pagination skips page 1, restricts all queries to 10 items, and returns results in reverse chronological order.
* **Recommended Solution**: Correct the offset calculations, use the dynamic limit, and sort in ascending order.
* **Example Fix**:
```python
items = (
    base.order_by(Booking.start_time.asc(), Booking.id.asc())
    .offset((page - 1) * limit)
    .limit(limit)
    .all()
)
```

---

### 8. Overwriting Booking Start Time in Detail Endpoint
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 166
* **Severity**: **High**
* **Problem**: The booking detail endpoint overwrites `response["start_time"]` with `booking.created_at`.
* **Impact**: When fetching booking details, the response shows the booking creation time instead of when the reservation actually starts.
* **Recommended Solution**: Remove the erroneous overwrite line. `serialize_booking` already sets the correct start time.
* **Example Fix**:
```python
# Remove this line entirely:
# response["start_time"] = iso_utc(booking.created_at)
```

---

### 9. Broken Cancellation Refund notice and Fallback
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 199-206
* **Severity**: **High**
* **Problem**:
  1. The 100% refund logic checks if `notice_hours > 48`. A notice of exactly 48 hours evaluates to false, incorrectly giving only a 50% refund.
  2. The `else` block fallback gives a 50% refund instead of 0% for cancellations made with less than 24 hours' notice.
* **Impact**: Violates business rule 6, leading to incorrect refund amounts and financial loss for the coworking provider.
* **Recommended Solution**: Perform exact `timedelta` comparisons and set the fallback to 0.
* **Example Fix**:
```python
if notice >= timedelta(hours=48):
    refund_percent = 100
elif notice >= timedelta(hours=24):
    refund_percent = 50
else:
    refund_percent = 0
```

---

### 10. Mismatch in Refund Rounding Logic
* **File Path**: `app/routers/bookings.py` (Line 208) vs `app/services/refunds.py` (Lines 15-17)
* **Severity**: **High**
* **Problem**: The cancellation router calculates refunds using `round()` (banker's rounding), while the ledger service calculates them by truncating the values using `int()`.
* **Impact**: Violates business rule 6 ("refund amount returned by the cancel response must equal the amount stored in the RefundLog" and "half-cents rounding up"). For odd numbers, the response and database will mismatch (e.g. 38 cents vs 37 cents).
* **Recommended Solution**: Use a consistent round-half-up utility function in both places.
* **Example Fix**:
```python
# In a shared utility module or timeutils.py
def round_half_up(value: float) -> int:
    return int(value + 0.5)

# In bookings.py
refund_amount_cents = round_half_up(booking.price_cents * (refund_percent / 100.0))

# In app/services/refunds.py
def log_refund(db: Session, booking: Booking, percent: int) -> RefundLog:
    amount_cents = round_half_up(booking.price_cents * (percent / 100.0))
    ...
```

---

### 11. Concurrency Deadlock in Notifications Service
* **File Path**: `app/services/notifications.py`
* **Line Number(s)**: 24-36
* **Severity**: **Critical**
* **Problem**: `notify_created` acquires locks in the order `_email_lock` -> `_audit_lock`, while `notify_cancelled` acquires them in the reverse order `_audit_lock` -> `_email_lock`.
* **Impact**: If a booking is created and another booking is cancelled concurrently, the application threads can block each other permanently, causing the entire service to hang.
* **Recommended Solution**: Do not nest the locks. Acquire them sequentially to prevent deadlocks.
* **Example Fix**:
```python
def notify_created(booking) -> None:
    with _email_lock:
        _send_email("created", booking)
    with _audit_lock:
        _write_audit("created", booking)

def notify_cancelled(booking) -> None:
    with _audit_lock:
        _write_audit("cancelled", booking)
    with _email_lock:
        _send_email("cancelled", booking)
```

---

### 12. Concurrency Race Condition in Reference Code Generation
* **File Path**: `app/services/reference.py`
* **Line Number(s)**: 17-21
* **Severity**: **Critical**
* **Problem**: `next_reference_code` reads the shared counter, sleeps for 120ms, and then increments it.
* **Impact**: Under concurrent requests, multiple threads will read the same counter value before it is incremented, generating duplicate reference codes. This violates business rule 7 ("reference_code is unique") and introduces an artificial 120ms bottleneck.
* **Recommended Solution**: Synchronize the counter increment using a thread lock, and remove the artificial delay.
* **Example Fix**:
```python
import threading
_counter_lock = threading.Lock()

def next_reference_code() -> str:
    with _counter_lock:
        current = _counter["value"]
        _counter["value"] = current + 1
    return f"CW-{current:06d}"
```

---

### 13. Concurrency Race Conditions and Volatile State in Stats Service
* **File Path**: `app/services/stats.py`
* **Line Number(s)**: 15-26
* **Severity**: **Critical**
* **Problem**:
  1. Updating and cancelling bookings reads, sleeps for 100ms, and writes back stats without synchronization.
  2. Stats are stored in a volatile in-memory dictionary `_stats` that is lost on application restart.
* **Impact**: Concurrent requests will overwrite stats, causing metrics to become inaccurate. Additionally, after an application restart, stats are reset to 0, violating consistency requirements.
* **Recommended Solution**: Query statistical aggregates directly from the database, or use a lock to update stats and reload them from the database on startup.
* **Example Fix**:
```python
# Query directly from the DB inside app/routers/rooms.py (safest and most robust)
from sqlalchemy import func
from ..models import Booking

# Inside stats.py or rooms.py:
def get_room_stats(db: Session, room_id: int) -> dict:
    row = (
        db.query(
            func.count(Booking.id).label("count"),
            func.sum(Booking.price_cents).label("revenue")
        )
        .filter(Booking.room_id == room_id, Booking.status == "confirmed")
        .first()
    )
    return {
        "count": row.count or 0,
        "revenue": row.revenue or 0
    }
```

---

### 14. Security Bypass: Cross-Organization CSV Export Leaks Data
* **File Path**: `app/services/export.py`
* **Line Number(s)**: 22-29, 48-50
* **Severity**: **Critical**
* **Problem**: When exporting booking data with `include_all=true` and a specified `room_id`, the system calls `fetch_bookings_raw(db, room_id)`. This query retrieves bookings without verifying that the room belongs to the admin's organization.
* **Impact**: An administrator from one organization can export the entire booking history of a room belonging to a competitor organization by passing its ID in the URL parameter.
* **Recommended Solution**: Scope the query inside `fetch_bookings_raw` to ensure it only retrieves rooms within the admin's organization.
* **Example Fix**:
```python
def fetch_bookings_raw(db: Session, room_id: int, org_id: int) -> list[Booking]:
    return (
        db.query(Booking)
        .join(Room)
        .filter(Booking.room_id == room_id, Room.org_id == org_id)
        .order_by(Booking.id.asc())
        .all()
    )
```

---

### 15. Stale Room Availability Cache on Cancellation
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 216-218
* **Severity**: **High**
* **Problem**: The cancellation route invalidates the usage report cache but does not invalidate the room's availability cache.
* **Impact**: The room availability endpoint will continue to show the cancelled time slot as busy (cached) until the cache expires.
* **Recommended Solution**: Invalidate the availability cache when a booking is cancelled.
* **Example Fix**:
```python
cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())
```

---

### 16. Stale Usage Report Cache on Booking Creation
* **File Path**: `app/routers/bookings.py`
* **Line Number(s)**: 119-122
* **Severity**: **Medium**
* **Problem**: Creating a new booking does not invalidate the organization's usage report cache.
* **Impact**: Admins will see outdated reports that do not include newly created bookings.
* **Recommended Solution**: Invalidate the usage report cache when a booking is created.
* **Example Fix**:
```python
cache.invalidate_report(user.org_id)
```

---

### 17. Incomplete Availability Queries Across Date Boundaries
* **File Path**: `app/routers/rooms.py`
* **Line Number(s)**: 80-90
* **Severity**: **High**
* **Problem**: The availability check filters bookings by `Booking.start_time >= day_start` and `Booking.start_time < day_end`.
* **Impact**: Bookings that start on the previous day but end on the requested day (overlapping the date boundary) are not retrieved. This displays the room as available when it is actually occupied, allowing double-bookings.
* **Recommended Solution**: Filter queries to fetch any booking that overlaps with the requested date range.
* **Example Fix**:
```python
bookings = (
    db.query(Booking)
    .filter(
        Booking.room_id == room.id,
        Booking.status == "confirmed",
        Booking.start_time < day_end,
        Booking.end_time > day_start,
    )
    .order_by(Booking.start_time.asc(), Booking.id.asc())
    .all()
)
```

---

### 18. Potential Server Crash on Invalid Subject Cast
* **File Path**: `app/auth.py`
* **Line Number(s)**: 106
* **Severity**: **Medium**
* **Problem**: The authentication dependency converts the JWT's `sub` claim directly into an integer using `int(payload["sub"])` without handling exceptions.
* **Impact**: If a client sends a request with a validly signed JWT that has a non-integer `sub` claim (e.g. `"alice"`), the server will throw an unhandled `ValueError` and crash with a `500 Internal Server Error` instead of returning a `401 Unauthorized` response.
* **Recommended Solution**: Catch `ValueError` when casting `sub` to an integer and raise a `401` error.
* **Example Fix**:
```python
try:
    user_id = int(payload["sub"])
except ValueError:
    raise AppError(401, "UNAUTHORIZED", "Invalid token subject ID")
user = db.query(User).filter(User.id == user_id).first()
```

---

## 12. Suggestions for Long-Term Code Quality Improvements

1. **Adopt PostgreSQL**: Migrate from SQLite to PostgreSQL. This supports native row locking (`select_for_update`) to prevent booking overlaps and quota race conditions under load.
2. **Implement Redis Caching & Session Store**: Shift rate limiting, token blacklists, and report caching to Redis. This keeps state consistent across multiple server instances and prevents data loss during restarts.
3. **Database Migrations (Alembic)**: Integrate Alembic to manage database migrations systematically.
4. **Remove Artificial Latencies**: Remove the `time.sleep` calls in the services. These artificial delays slow down response times and worsen concurrency race windows.
5. **Add Integration Tests**: Expand testing coverage to include concurrent booking requests, rate limits, and cross-organization access attempts.

---

## 13. Overall Project Assessment & Scores

| Dimension | Score (0-10) | Rationale |
|---|---|---|
| **Code Quality** | **4 / 10** | The code has clean separation of concerns, but is riddled with critical bugs, copy-paste errors, and incorrect logic (such as wrong timezone conversions and broken pagination). |
| **Architecture** | **5 / 10** | Layered routing/service structure is good. However, storing critical application states (blacklists, rates, statistics) in-memory makes the system volatile and unfit for scaling horizontally. |
| **Maintainability** | **6 / 10** | Clear layouts, separation of concerns, and descriptive naming conventions make it easy to modify, but the lack of database migrations and unit test coverage makes updates risky. |
| **Security** | **2 / 10** | Critical security issues are present, including a broken token revocation check that renders logouts useless, missing refresh token invalidations, and an export endpoint that allows cross-tenant data theft. |
| **Performance** | **3 / 10** | The API has artificial 100ms-120ms delays injected directly into critical paths. Additionally, SQLite table locking restricts write throughput under load. |
| **Scalability** | **2 / 10** | In-memory locks, volatile caching dictionary states, and local SQLite files make it impossible to deploy this application behind a load balancer with multiple instances. |
| **Readability** | **8 / 10** | The code is readable, concise, and follows standard PEP 8 naming conventions. |
| **Production Readiness** | **2 / 10** | Due to data isolation flaws, concurrency deadlocks, and volatile states, this application is not suitable for production deployment in its current state. |
