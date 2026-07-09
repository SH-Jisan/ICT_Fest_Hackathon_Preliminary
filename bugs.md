### Bug #1

**Bug Name:** Access Token Expiry Mismatch
**Severity:** High

**Affected File(s):**

```text
app/auth.py
```

**Line(s):**

```text
Line 71
```

**Problem (1–2 lines):**
The access token expiration lifetime was erroneously calculated as 900 minutes (15 hours) instead of 900 seconds (15 minutes), violating the 15-minute token ...

**Original (Buggy) Code:**

```python
    lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
```

**Fixed Code:**

```python
    lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

**Fix Summary (1–2 lines):**
Removed the `* 60` multiplier to correctly evaluate the duration to exactly 15 minutes (900 seconds).

---
### Bug #2

**Bug Name:** Stale Room Availability Cache on Cancellation
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 230
```

**Problem (1–2 lines):**
The room availability endpoint `GET /rooms/{id}/availability` returned stale cached busy schedules because the booking cancellation endpoint did not invalida...

**Original (Buggy) Code:**

```python
    stats.record_cancel(booking.room_id, booking.price_cents)
    cache.invalidate_report(user.org_id)
    notifications.notify_cancelled(booking)
```

**Fixed Code:**

```python
    stats.record_cancel(booking.room_id, booking.price_cents)
    cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())
    cache.invalidate_report(user.org_id)
    notifications.notify_cancelled(booking)
```

**Fix Summary (1–2 lines):**
Added `cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())` inside `cancel_booking`.

---
### Bug #3

**Bug Name:** Back-to-Back Booking Incorrectly Rejected
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 49–51
```

**Problem (1–2 lines):**
An identified bug in the application.

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Changed the logic to use strict `<` comparison operators: `if b.start_time < end and start < b.end_time: return True`.

---
### Bug #4

**Bug Name:** Zero/Negative Booking Durations Allowed
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 94–95
```

**Problem (1–2 lines):**
An identified bug in the application.

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Changed the assertion check from `duration_hours > MAX_DURATION_HOURS` to `not (1 <= duration_hours <= MAX_DURATION_HOURS)`.

---
### Bug #5

**Bug Name:** Missing booking end_time Sequence Validation
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 89–90
```

**Problem (1–2 lines):**
An identified bug in the application.

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Added an explicit validation check: `if end <= start: raise AppError(400, "INVALID_BOOKING_WINDOW", "end_time must be strictly after start_time")`.

---
### Bug #6

**Bug Name:** Incorrect Booking Sorting Order
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 146
```

**Problem (1–2 lines):**
The bookings query sorted results using descending start times (`start_time.desc()`), while the specification required ascending start times (`start_time ASC...

**Original (Buggy) Code:**

```python
base.order_by(Booking.start_time.desc(), Booking.id.asc())
```

**Fixed Code:**

```python
base.order_by(Booking.start_time.asc(), Booking.id.asc())
```

**Fix Summary (1–2 lines):**
Updated sorting inside `list_bookings` query to use `Booking.start_time.asc()`.

---
### Bug #7

**Bug Name:** Member Booking Detail Authorization Bypass
**Severity:** Critical

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 171–175
```

**Problem (1–2 lines):**
The endpoint `GET /bookings/{booking_id}` loaded details for any booking in the organization without ensuring that members can only read their own bookings. ...

**Original (Buggy) Code:**

```python
    booking = (
        db.query(Booking)
        .join(Room, Booking.room_id == Room.id)
        .filter(Booking.id == booking_id, Room.org_id == user.org_id)
        .first()
    )
    if booking is None:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")
```

**Fixed Code:**

```python
    booking = (
        db.query(Booking)
        .join(Room, Booking.room_id == Room.id)
        .filter(Booking.id == booking_id, Room.org_id == user.org_id)
        .first()
    )
    if booking is None:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")

    if user.role != "admin" and booking.user_id != user.id:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")
```

**Fix Summary (1–2 lines):**
Added validation to check if the caller is not an admin and is not the owner of the booking, raising a `404 BOOKING_NOT_FOUND` error if they are unauthorized.

---
### Bug #8

**Bug Name:** Missing Booking Quota Test Coverage
**Severity:** Low

**Affected File(s):**

```text
tests/test_smoke.py
```

**Line(s):**

```text
Lines 223–296
```

**Problem (1–2 lines):**
The integration test suite did not contain any checks to verify that booking quota validations, limits, boundaries, or exclusions (like bookings outside the ...

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Appended the `test_booking_quota_limits` function to `tests/test_smoke.py` to cover all limits, boundary dates, HTTP 409 responses, and success paths outside...

---
### Bug #9

**Bug Name:** Single Booking Detail Overwrites `start_time`
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 179
```

**Problem (1–2 lines):**
The endpoint `GET /bookings/{booking_id}` returned the wrong `start_time` in its response payload because it overrode the serialized start time with the crea...

**Original (Buggy) Code:**

```python
    response = serialize_booking(booking)
    response["start_time"] = iso_utc(booking.created_at)
```

**Fixed Code:**

```python
    response = serialize_booking(booking)
```

**Fix Summary (1–2 lines):**
Removed the assignment line `response["start_time"] = iso_utc(booking.created_at)` from the endpoint router.

---
### Bug #10

**Bug Name:** Booking start_time Past Grace Window Allowed
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 92–93
```

**Problem (1–2 lines):**
An identified bug in the application.

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Removed the `- timedelta(seconds=300)` subtraction offset, changing the check to a direct comparison: `if start <= now`.

---
### Bug #11

**Bug Name:** Concurrent Cancellation State Race Condition
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
app/services/refunds.py
```

**Line(s):**

```text
Lines 196–228
 refunds.py : Lines 15–24
```

**Problem (1–2 lines):**
The cancellation endpoint queried the booking, checked if it was already cancelled, created a refund entry, slept during a simulated settlement pause, update...

**Original (Buggy) Code:**

```python
# In bookings.py (outside lock):
    booking = (
        db.query(Booking)
        .join(Room, Booking.room_id == Room.id)
        .filter(Booking.id == booking_id, Room.org_id == user.org_id)
        .first()
    )
...
    with _booking_lock:
        if booking.status == "cancelled":
...
        log_refund(db, booking, refund_percent)
```

**Fixed Code:**

```python
# In bookings.py:
    with _booking_lock:
        booking = (
            db.query(Booking)
            .join(Room, Booking.room_id == Room.id)
            .filter(Booking.id == booking_id, Room.org_id == user.org_id)
            .first()
        )
...
        if booking.status == "cancelled":
            raise AppError(409, "ALREADY_CANCELLED", "Booking already cancelled")
...
        refund = log_refund(db, booking, refund_percent)
        refund_amount_cents = refund.amount_cents
        _settlement_pause()
        booking.status = "cancelled"
        db.commit()
```

**Fix Summary (1–2 lines):**
Moved the database query, permission verification, state validation check, `log_refund` invocation, and the single final `db.commit()` inside the synchronize...

---
### Bug #12

**Bug Name:** Concurrent Booking Race Condition
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 26, 108–127
```

**Problem (1–2 lines):**
An identified bug in the application.

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Defined a global `_booking_lock = threading.Lock()` and wrapped the validation checks (`_has_conflict` and `_check_quota`), reference generation, and databas...

---
### Bug #13

**Bug Name:** Concurrent Booking Cancellation Race Condition
**Severity:** Critical

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 204–224
```

**Problem (1–2 lines):**
The cancellation route validated status and executed updates without synchronization, allowing concurrent requests to bypass status checks and write duplicat...

**Original (Buggy) Code:**

```python
    if booking.status == "cancelled":
        raise AppError(409, "ALREADY_CANCELLED", "Booking already cancelled")
    ...
    log_refund(db, booking, refund_percent)
    booking.status = "cancelled"
    db.commit()
```

**Fixed Code:**

```python
    with _booking_lock:
        if booking.status == "cancelled":
            raise AppError(409, "ALREADY_CANCELLED", "Booking already cancelled")
        ...
        log_refund(db, booking, refund_percent)
        booking.status = "cancelled"
        db.commit()
```

**Fix Summary (1–2 lines):**
Wrapped validations and commits under `_booking_lock`.

---
### Bug #14

**Bug Name:** Cross-Organization CSV Export Data Leak
**Severity:** Critical

**Affected File(s):**

```text
app/services/export.py
```

**Line(s):**

```text
Lines 22–30, 50–51
```

**Problem (1–2 lines):**
The admin export service did not filter bookings by organization boundaries when a specific room ID was requested with `include_all=True`. It retrieved compe...

**Original (Buggy) Code:**

```python
def fetch_bookings_raw(db: Session, room_id: int) -> list[Booking]:
    """Load every booking for a single room, ordered by id."""
    return (
        db.query(Booking)
        .filter(Booking.room_id == room_id)
        .order_by(Booking.id.asc())
        .all()
    )
...
    if include_all:
        if room_id is not None:
            rows = fetch_bookings_raw(db, room_id)
```

**Fixed Code:**

```python
def fetch_bookings_raw(db: Session, org_id: int, room_id: int) -> list[Booking]:
    """Load every booking for a single room, ordered by id."""
    return (
        db.query(Booking)
        .join(Room)
        .filter(Booking.room_id == room_id, Room.org_id == org_id)
        .order_by(Booking.id.asc())
        .all()
    )
...
    if include_all:
        if room_id is not None:
            rows = fetch_bookings_raw(db, org_id, room_id)
```

**Fix Summary (1–2 lines):**
Modified `fetch_bookings_raw` to accept `org_id` and filter on `Room.org_id == org_id` via a SQL join.

---
### Bug #15

**Bug Name:** Nested Lock Circular Deadlock in Notifications
**Severity:** Critical

**Affected File(s):**

```text
app/services/notifications.py
```

**Line(s):**

```text
Lines 24–35
```

**Problem (1–2 lines):**
The notification service acquired `_email_lock` and `_audit_lock` in nested, reverse order between `notify_created` (email -> audit) and `notify_cancelled` (...

**Original (Buggy) Code:**

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

**Fixed Code:**

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

**Fix Summary (1–2 lines):**
De-nested the lock acquisitions so they are acquired sequentially and independently.

---
### Bug #16

**Bug Name:** Flawed Access Token Revocation Check
**Severity:** Critical

**Affected File(s):**

```text
app/auth.py
```

**Line(s):**

```text
Lines 105–120
```

**Problem (1–2 lines):**
The system checked if a user's `sub` (User ID string) existed inside `_revoked_tokens` to detect logged-out tokens. Since `_revoked_tokens` stores token `jti...

**Original (Buggy) Code:**

```python
def revoke_access_token(payload: dict) -> None:
    _revoked_tokens.add(payload["jti"])

def get_token_payload(request: Request) -> dict:
    ...
    if payload.get("sub") in _revoked_tokens:
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
```

**Fixed Code:**

```python
def revoke_access_token(payload: dict) -> None:
    check_and_revoke_token(payload.get("jti"))

def get_token_payload(request: Request) -> dict:
    ...
    if is_token_revoked(payload.get("jti")):
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
```

**Fix Summary (1–2 lines):**
Updated the verification logic to query `is_token_revoked` using `jti`, and synchronized updates under a global thread lock.

---
### Bug #17

**Bug Name:** Flawed Offset Math Skips Page 1 Results
**Severity:** Critical

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 147
```

**Problem (1–2 lines):**
The offset was calculated as `page * limit`, skipping the first page of results entirely (for page 1 and limit 10, offset evaluated to 10).

**Original (Buggy) Code:**

```python
.offset(page * limit)
```

**Fixed Code:**

```python
.offset((page - 1) * limit)
```

**Fix Summary (1–2 lines):**
Changed offset calculations to use `(page - 1) * limit`.

---
### Bug #18

**Bug Name:** Hardcoded Query Limit Ignores User Input
**Severity:** Critical

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 148
```

**Problem (1–2 lines):**
The bookings listing query hardcoded `.limit(10)`, completely ignoring the user-supplied `limit` query parameters.

**Original (Buggy) Code:**

```python
.limit(10)
```

**Fixed Code:**

```python
.limit(limit)
```

**Fix Summary (1–2 lines):**
Replaced the hardcoded constant with the validated `limit` variable.

---
### Bug #19

**Bug Name:** Rate Limiter Race Condition
**Severity:** Critical

**Affected File(s):**

```text
app/services/ratelimit.py
```

**Line(s):**

```text
Lines 10, 20–28
```

**Problem (1–2 lines):**
The rate limiter read and modified the volatile user request bucket without synchronization, allowing concurrent requests to bypass the limit.

**Original (Buggy) Code:**

```python
def record_and_check(user_id: int) -> None:
    now = time.time()
    bucket = _buckets.get(user_id, [])
    bucket = [t for t in bucket if t > now - _WINDOW_SECONDS]
    _settle_pause()
    bucket.append(now)
    _buckets[user_id] = bucket
    if len(bucket) > _MAX_REQUESTS:
        raise AppError(429, "RATE_LIMITED", "Too many booking requests")
```

**Fixed Code:**

```python
_limiter_lock = threading.Lock()

def record_and_check(user_id: int) -> None:
    with _limiter_lock:
        now = time.time()
        bucket = _buckets.get(user_id, [])
        bucket = [t for t in bucket if t > now - _WINDOW_SECONDS]
        _settle_pause()
        bucket.append(now)
        _buckets[user_id] = bucket
        if len(bucket) > _MAX_REQUESTS:
            raise AppError(429, "RATE_LIMITED", "Too many booking requests")
```

**Fix Summary (1–2 lines):**
Synchronized state modifications using a global `threading.Lock`.

---
### Bug #20

**Bug Name:** Missing Reference Code Collision Recovery
**Severity:** Critical

**Affected File(s):**

```text
app/services/reference.py
app/routers/bookings.py
```

**Line(s):**

```text
Lines 28–35
 bookings.py : Line 121
```

**Problem (1–2 lines):**
The system did not check if a generated reference code existed before writing it to the database, causing raw IntegrityError database exceptions to crash the...

**Original (Buggy) Code:**

```python
# In bookings.py:
reference_code=reference.next_reference_code()
```

**Fixed Code:**

```python
# In reference.py:
        while True:
            current = _counter["value"]
            _format_pause()
            _counter["value"] = current + 1
            code = f"CW-{current:06d}"

            from ..models import Booking
            exists = db.query(Booking).filter(Booking.reference_code == code).first()
            if not exists:
                return code

# In bookings.py:
            reference_code=reference.next_reference_code(db),
```

**Fix Summary (1–2 lines):**
Implemented a check-and-retry database loop inside `next_reference_code`.

---
### Bug #21

**Bug Name:** Reference Code Volatility on Restart
**Severity:** High

**Affected File(s):**

```text
app/services/reference.py
```

**Line(s):**

```text
Lines 5–27
```

**Problem (1–2 lines):**
The booking reference code generator stored the counter in volatile in-memory dictionary `_counter = {"value": 1000}`. If the application server restarted, t...

**Original (Buggy) Code:**

```python
_counter = {"value": 1000}

def next_reference_code() -> str:
    current = _counter["value"]
    _format_pause()
    _counter["value"] = current + 1
    return f"CW-{current:06d}"
```

**Fixed Code:**

```python
_counter = {"value": 1000}
_reference_lock = threading.Lock()

def next_reference_code(db: Session) -> str:
    with _reference_lock:
        if _counter["value"] == 1000:
            from ..models import Booking
            max_ref = db.query(Booking.reference_code).order_by(Booking.reference_code.desc()).first()
            if max_ref and max_ref[0]:
                try:
                    code_num = int(max_ref[0].split("-")[1])
                    _counter["value"] = max(code_num + 1, _counter["value"])
                except (IndexError, ValueError):
                    pass

        while True:
            current = _counter["value"]
            _format_pause()
            _counter["value"] = current + 1
            code = f"CW-{current:06d}"
            
            # Check collisions...
```

**Fix Summary (1–2 lines):**
Added database seeding logic on first generator execution: queries the highest reference code prefix from the database and sets the monotonic counter startin...

---
### Bug #22

**Bug Name:** Missing Refresh Token Rotation and Replay Protection
**Severity:** Critical

**Affected File(s):**

```text
app/routers/auth.py
app/auth.py
```

**Line(s):**

```text
Lines 23–45
 routers/auth.py : Lines 81–96
```

**Problem (1–2 lines):**
The refresh endpoint decoded tokens and returned new credentials without revoking or marking the old refresh token as used. Users could reuse the same refres...

**Original (Buggy) Code:**

```python
# In routers/auth.py:
@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Wrong token type")
    user = db.query(User).filter(User.id == int(data["sub"])).first()
    ...
```

**Fixed Code:**

```python
# In auth.py:
def check_and_revoke_token(jti: str) -> bool:
    if not jti:
        return False
    with _revocation_lock:
        if jti in _revoked_tokens:
            return False
        _revoked_tokens.add(jti)
        return True

# In routers/auth.py:
@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Wrong token type")
    
    if not check_and_revoke_token(data.get("jti")):
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
    ...
```

**Fix Summary (1–2 lines):**
Implemented a synchronized, atomic `check_and_revoke_token` block that revokes the token `jti` on first use and rejects subsequent reuse attempts.

---
### Bug #23

**Bug Name:** Incorrect Refund Notice Thresholds and Fallback
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 207–214
```

**Problem (1–2 lines):**
The cancellation router verified the 48-hour notice threshold using `notice_hours > 48` (which failed for exactly 48 hours), and set the default fallback ref...

**Original (Buggy) Code:**

```python
    now = datetime.utcnow()
    notice = booking.start_time - now
    notice_hours = int(notice.total_seconds() // 3600)
    if notice_hours > 48:
        refund_percent = 100
    elif notice >= timedelta(hours=24):
        refund_percent = 50
    else:
        refund_percent = 50
```

**Fixed Code:**

```python
    now = datetime.utcnow()
    notice = booking.start_time - now
    if notice >= timedelta(hours=48):
        refund_percent = 100
    elif notice >= timedelta(hours=24):
        refund_percent = 50
    else:
        refund_percent = 0
```

**Fix Summary (1–2 lines):**
Changed the logic to use exact `timedelta` comparisons and set the fallback percent to `0`.

---
### Bug #24

**Bug Name:** Refund Cents Rounding Strategy Mismatch
**Severity:** High

**Affected File(s):**

```text
app/timeutils.py
app/routers/bookings.py
app/services/refunds.py
```

**Line(s):**

```text
Lines 20–25
 bookings.py : Lines 216
 refunds.py : Lines 12–15
```

**Problem (1–2 lines):**
The cancellation router used Python's default banker's rounding, while the database ledger service truncated decimals using `int()`, creating mismatches in s...

**Original (Buggy) Code:**

```python
# In bookings.py:
refund_amount_cents = round(booking.price_cents * (refund_percent / 100.0))

# In refunds.py:
dollars = booking.price_cents / 100.0
refund_dollars = dollars * (percent / 100.0)
amount_cents = int(refund_dollars * 100)
```

**Fixed Code:**

```python
# In timeutils.py:
def round_half_up(value: float) -> int:
    return int(value + 0.5)

# In bookings.py:
refund_amount_cents = round_half_up(booking.price_cents * (refund_percent / 100.0))

# In refunds.py:
amount_cents = round_half_up(booking.price_cents * (percent / 100.0))
```

**Fix Summary (1–2 lines):**
Implemented a shared `round_half_up` function and utilized it in both modules.

---
### Bug #25

**Bug Name:** Non-Atomic User Registration Commits
**Severity:** High

**Affected File(s):**

```text
app/routers/auth.py
```

**Line(s):**

```text
Lines 30–35
```

**Problem (1–2 lines):**
The user registration endpoint committed organization creation to the database *before* executing the user insert query, resulting in orphan organization row...

**Original (Buggy) Code:**

```python
    if org is None:
        org = Organization(name=payload.org_name)
        db.add(org)
        db.commit()
        db.refresh(org)
```

**Fixed Code:**

```python
        if org is None:
            org = Organization(name=org_name)
            db.add(org)
            db.flush()
        ...
        db.add(user)
        db.commit()
```

**Fix Summary (1–2 lines):**
Removed the intermediary `db.commit()` on organization creation, using `db.flush()` instead to allocate IDs, committing both additions atomically at the end.

---
### Bug #26

**Bug Name:** Uncaught Database Integrity Exceptions on Concurrent Registrations
**Severity:** High

**Affected File(s):**

```text
app/routers/auth.py
```

**Line(s):**

```text
Lines 24–75
```

**Problem (1–2 lines):**
Concurrent attempts to register identical organizations or usernames triggered database unique constraints, causing requests to crash with uncaught 500 errors.

**Original (Buggy) Code:**

```python
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Raw queries and database updates without error handling
```

**Fixed Code:**

```python
    try:
        ...
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handle concurrent registration collisions
        org = db.query(Organization).filter(Organization.name == org_name).first()
        if org is not None:
            existing = (
                db.query(User)
                .filter(User.org_id == org.id, User.username == username)
                .first()
            )
            if existing is not None:
                raise AppError(409, "USERNAME_TAKEN", "Username taken")
            
            try:
                user = User(
                    org_id=org.id,
                    username=username,
                    hashed_password=hash_password(payload.password),
                    role="member",
                )
                db.add(user)
                db.commit()
            except IntegrityError:
                db.rollback()
                raise AppError(409, "USERNAME_TAKEN", "Username taken")
        else:
            raise AppError(409, "USERNAME_TAKEN", "Username taken")
```

**Fix Summary (1–2 lines):**
Wrapped registration logic in a `try/except IntegrityError` block. If organization name collision occurs, the database rolls back, loads the existing organiz...

---
### Bug #27

**Bug Name:** Resource Enumeration on Room CSV Export
**Severity:** High

**Affected File(s):**

```text
app/routers/admin.py
```

**Line(s):**

```text
Lines 69–74
```

**Problem (1–2 lines):**
The export endpoint accepted a `room_id` query parameter and generated a CSV report without verifying that the room belonged to the administrator's organizat...

**Original (Buggy) Code:**

```python
@router.get("/export")
def export(
    room_id: int | None = Query(None),
    include_all: bool = Query(False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    csv_body = generate_export(db, admin.org_id, admin.id, room_id, include_all)
    return Response(content=csv_body, media_type="text/csv")
```

**Fixed Code:**

```python
@router.get("/export")
def export(
    room_id: int | None = Query(None),
    include_all: bool = Query(False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if room_id is not None:
        room = db.query(Room).filter(Room.id == room_id, Room.org_id == admin.org_id).first()
        if room is None:
            raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
            
    csv_body = generate_export(db, admin.org_id, admin.id, room_id, include_all)
    return Response(content=csv_body, media_type="text/csv")
```

**Fix Summary (1–2 lines):**
Added a check to query the room by ID and organization ID, raising a `404 ROOM_NOT_FOUND` if the room does not exist in the admin's organization scope.

---
### Bug #28

**Bug Name:** Room Stats Lost Updates Concurrency Race Condition
**Severity:** Critical

**Affected File(s):**

```text
app/services/stats.py
```

**Line(s):**

```text
Lines 6–30
```

**Problem (1–2 lines):**
The statistics update functions fetched state, paused artificially, and overwrote process memory, causing concurrent bookings to collision-overwrite each oth...

**Original (Buggy) Code:**

```python
def record_create(room_id: int, price_cents: int) -> None:
    current = _stats.get(room_id, {"count": 0, "revenue": 0})
    count, revenue = current["count"], current["revenue"]
    _aggregate_pause()
    _stats[room_id] = {"count": count + 1, "revenue": revenue + price_cents}
```

**Fixed Code:**

```python
# Retained record_create and record_cancel as no-op placeholders for backward compatibility.
# Statistics are computed on-demand from the SQL database using:
def get(db: Session, room_id: int) -> dict:
    row = (
        db.query(
            func.count(Booking.id).label("count"),
            func.coalesce(func.sum(Booking.price_cents), 0).label("revenue"),
        )
        .filter(Booking.room_id == room_id, Booking.status == "confirmed")
        .first()
    )
    return {"count": row.count or 0, "revenue": row.revenue or 0}
```

**Fix Summary (1–2 lines):**
Changed the backend design to fetch aggregates directly from the database using SQL queries, resolving concurrent race conditions entirely by relying on data...

---
### Bug #29

**Bug Name:** In-Memory Room Stats Persistence and Consistency Failure
**Severity:** Critical

**Affected File(s):**

```text
app/services/stats.py
app/routers/rooms.py
```

**Line(s):**

```text
Lines 6–30
 rooms.py : Lines 109–115
```

**Problem (1–2 lines):**
The room statistics endpoint returned data stored inside an in-memory process-local dictionary. A server restart completely wiped all statistics, causing sta...

**Original (Buggy) Code:**

```python
# In stats.py:
_stats: dict[int, dict] = {}
...
def get(room_id: int) -> dict:
    return _stats.get(room_id, {"count": 0, "revenue": 0})

# In routers/rooms.py:
    room = _get_org_room(db, room_id, user.org_id)
    current = stats.get(room.id)
    return {
        "room_id": room.id,
        "total_confirmed_bookings": current["count"],
        "total_revenue_cents": current["revenue"],
    }
```

**Fixed Code:**

```python
# In stats.py:
def get(db: Session, room_id: int) -> dict:
    row = (
        db.query(
            func.count(Booking.id).label("count"),
            func.coalesce(func.sum(Booking.price_cents), 0).label("revenue"),
        )
        .filter(Booking.room_id == room_id, Booking.status == "confirmed")
        .first()
    )
    return {"count": row.count or 0, "revenue": row.revenue or 0}

# In routers/rooms.py:
    room = _get_org_room(db, room_id, user.org_id)
    current = stats.get(db, room.id)
    return {
        "room_id": room.id,
        "confirmed_booking_count": current["count"],
        "total_price_cents": current["revenue"],
        "total_confirmed_bookings": current["count"],
        "total_revenue_cents": current["revenue"],
    }
```

**Fix Summary (1–2 lines):**
Re-implemented the `get` stats function to perform a database query using SQL aggregations (`COUNT` and `SUM` wrapped in `coalesce` to default to 0), and upd...

---
### Bug #30

**Bug Name:** Unhandled ValueError on Malformed ISO 8601 Datetime String
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Lines 81–84
```

**Problem (1–2 lines):**
The booking creation endpoint crashed with a `500 Internal Server Error` instead of returning a proper validation error when given a malformed or invalid ISO...

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Wrapped the `parse_input_datetime` calls inside a `try-except ValueError` block and raised `AppError(400, "INVALID_BOOKING_WINDOW", "Invalid datetime format"...

---
### Bug #31

**Bug Name:** Potential Internal Server Crash on Non-Integer Token Subject
**Severity:** Medium

**Affected File(s):**

```text
app/auth.py
app/routers/auth.py
```

**Line(s):**

```text
Lines 127–130
 routers/auth.py : Line 120
```

**Problem (1–2 lines):**
The application decoded the `sub` claim from the JWT (which is specified to be a user ID string) and parsed it directly using `int(payload["sub"])` without a...

**Original (Buggy) Code:**

```python
# In app/auth.py:
user = db.query(User).filter(User.id == int(payload["sub"])).first()

# In app/routers/auth.py:
user = db.query(User).filter(User.id == int(data["sub"])).first()
```

**Fixed Code:**

```python
# In app/auth.py:
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise AppError(401, "UNAUTHORIZED", "Invalid token subject")
    user = db.query(User).filter(User.id == user_id).first()

# In app/routers/auth.py:
    try:
        user_id = int(data["sub"])
    except (ValueError, TypeError):
        raise AppError(401, "UNAUTHORIZED", "Invalid token subject")
    user = db.query(User).filter(User.id == user_id).first()
```

**Fix Summary (1–2 lines):**
Wrapped both conversion locations inside a `try/except (ValueError, TypeError)` block, raising a clean `AppError(401, "UNAUTHORIZED")` if parsing fails.

---
### Bug #32

**Bug Name:** Stale Usage Report Cache on Booking Creation
**Severity:** High

**Affected File(s):**

```text
app/routers/bookings.py
```

**Line(s):**

```text
Line 131
```

**Problem (1–2 lines):**
The administrator usage report endpoint returned stale cached data because the booking creation endpoint `POST /bookings` did not invalidate the report cache...

**Original (Buggy) Code:**

```python
    stats.record_create(room.id, price_cents)
    cache.invalidate_availability(room.id, start.date().isoformat())
    notifications.notify_created(booking)
```

**Fixed Code:**

```python
    stats.record_create(room.id, price_cents)
    cache.invalidate_availability(room.id, start.date().isoformat())
    cache.invalidate_report(user.org_id)
    notifications.notify_created(booking)
```

**Fix Summary (1–2 lines):**
Added `cache.invalidate_report(user.org_id)` invocation within `create_booking`.

---
### Bug #33

**Bug Name:** Success Response on Duplicate Username Registration
**Severity:** Critical

**Affected File(s):**

```text
app/routers/auth.py
```

**Line(s):**

```text
Lines 39–46
```

**Problem (1–2 lines):**
The registration endpoint returned a successful response containing the user's details when an existing username was submitted, bypassing uniqueness protecti...

**Original (Buggy) Code:**

```python
    existing = (
        db.query(User)
        .filter(User.org_id == org.id, User.username == payload.username)
        .first()
    )
    if existing is not None:
        return {
            "user_id": existing.id,
            "org_id": org.id,
            "username": existing.username,
            "role": existing.role,
        }
```

**Fixed Code:**

```python
        existing = (
            db.query(User)
            .filter(User.org_id == org.id, User.username == username)
            .first()
        )
        if existing is not None:
            raise AppError(409, "USERNAME_TAKEN", "Username taken")
```

**Fix Summary (1–2 lines):**
Changed the block to raise `AppError(409, "USERNAME_TAKEN", "Username taken")` if a duplicate username matches the organization id.

---
### Bug #34

**Bug Name:** Timezone Offset Dropped Without Normalization
**Severity:** High

**Affected File(s):**

```text
app/timeutils.py
```

**Line(s):**

```text
Lines 11–14
```

**Problem (1–2 lines):**
The datetime parsing utility dropped timezone offset metadata from incoming ISO 8601 string datetimes directly without converting the datetime to the UTC tim...

**Original (Buggy) Code:**

```python
# N/A
```

**Fixed Code:**

```python
# N/A
```

**Fix Summary (1–2 lines):**
Changed `.replace(tzinfo=None)` to `.astimezone(timezone.utc).replace(tzinfo=None)` when a timezone offset is present.
