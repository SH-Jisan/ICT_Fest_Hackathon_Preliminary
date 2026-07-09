1. Duplicate username registration is wrong

File: app/routers/auth.py
Lines: 37–43

Current code:

if existing is not None:
    return {
        "user_id": existing.id,
        "org_id": org.id,
        "username": existing.username,
        "role": existing.role,
    }

This is wrong because duplicate username inside the same organization must return:

409 USERNAME_TAKEN

But the current code returns the existing user as if registration succeeded.

Fix idea:

if existing is not None:
    raise AppError(409, "USERNAME_TAKEN", "Username already taken")

The rule clearly says duplicate username within the org must return 409 USERNAME_TAKEN.

2. Access token expiry is wrong

File: app/auth.py
Line: 50

Current code:

lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

ACCESS_TOKEN_EXPIRE_MINUTES = 15.

So this becomes:

15 * 60 minutes = 900 minutes

That means access token expires after 15 hours, not 900 seconds.

Expected:

Access token expiry = exactly 900 seconds = 15 minutes

Fix idea:

lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

or:

lifetime = timedelta(seconds=900)

The contract says access tokens must expire in exactly 900 seconds.

3. Logout does not actually revoke access token

File: app/auth.py
Lines: 85–98

Current revoke function stores the token jti:

def revoke_access_token(payload: dict) -> None:
    _revoked_tokens.add(payload["jti"])

But token validation checks sub, not jti:

if payload.get("sub") in _revoked_tokens:
    raise AppError(401, "UNAUTHORIZED", "Token has been revoked")

This means logout does not work. After logout, the same access token can still be used.

Fix idea:

if payload.get("jti") in _revoked_tokens:
    raise AppError(401, "UNAUTHORIZED", "Token has been revoked")

Logout must immediately invalidate the presented access token.

4. Refresh tokens are reusable

File: app/routers/auth.py
Lines: 81–93

Current refresh endpoint checks token type, then creates new tokens. But it never invalidates the old refresh token.

That violates this rule:

Refresh tokens are single-use.
Use refresh token once → success.
Use same refresh token again → 401.

Fix idea:

Add a revoked/used refresh token set, store refresh token jti, and reject reused refresh tokens.

Example logic:

_used_refresh_tokens = set()

def revoke_refresh_token(jti: str):
    _used_refresh_tokens.add(jti)

def is_refresh_revoked(jti: str):
    return jti in _used_refresh_tokens

Then inside /auth/refresh:

if data["jti"] in _used_refresh_tokens:
    raise AppError(401, "UNAUTHORIZED", "Refresh token already used")

_used_refresh_tokens.add(data["jti"])
5. Datetime timezone conversion is wrong

File: app/timeutils.py
Lines: 11–14

Current code:

dt = datetime.fromisoformat(value)
if dt.tzinfo is not None:
    dt = dt.replace(tzinfo=None)
return dt

This only removes timezone info. It does not convert to UTC.

Example:

2026-07-10T10:00:00+06:00

Correct UTC should be:

2026-07-10T04:00:00 UTC

But current code stores it as:

2026-07-10T10:00:00

That is 6 hours wrong.

Fix idea:

def parse_input_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

The problem statement says offset datetimes must be converted to UTC before storage/comparison.

6. Past booking has a 5-minute grace window, but rule says no grace window

File: app/routers/bookings.py
Lines: 84–87

Current code:

if start <= now - timedelta(seconds=300):
    raise AppError(...)

This means a booking that started 1–4 minutes ago is allowed.

But the rule says:

start_time must be strictly in the future — no grace window

Fix idea:

if start <= now:
    raise AppError(400, "INVALID_BOOKING_WINDOW", "start_time must be in the future")
7. Invalid booking duration is not fully checked

File: app/routers/bookings.py
Lines: 89–94

Current code checks whole number and maximum duration, but misses:

end_time must be strictly after start_time
minimum duration must be 1 hour

So these invalid bookings may pass:

start_time == end_time
end_time before start_time
0-hour booking
negative-duration booking

Fix idea:

if end <= start:
    raise AppError(400, "INVALID_BOOKING_WINDOW", "end_time must be after start_time")

duration_seconds = (end - start).total_seconds()

if duration_seconds % 3600 != 0:
    raise AppError(400, "INVALID_BOOKING_WINDOW", "duration must be a whole number of hours")

duration_hours = int(duration_seconds // 3600)

if duration_hours < 1 or duration_hours > 8:
    raise AppError(400, "INVALID_BOOKING_WINDOW", "duration out of range")

The rule requires whole-hour duration, minimum 1, maximum 8, and end_time > start_time.

8. Double-booking overlap logic is wrong

File: app/routers/bookings.py
Lines: 42–52

Current code:

if b.start_time <= end and start <= b.end_time:
    return True

This is wrong because it treats back-to-back bookings as conflicts.

Example:

Existing: 10:00–12:00
New:      12:00–14:00

This should be allowed, but current code blocks it.

Correct overlap formula:

existing.start_time < new.end_time AND new.start_time < existing.end_time

Fix idea:

if b.start_time < end and start < b.end_time:
    return True

Back-to-back bookings must be allowed.

9. Double-booking is not concurrency-safe

File: app/routers/bookings.py
Lines: 100–117

Even after fixing the overlap formula, the current flow is still unsafe:

Request A checks no conflict
Request B checks no conflict
A creates booking
B creates booking
Both succeed

That violates:

No double-booking must hold under concurrent requests.

Fix idea: use a lock/transaction around the full booking creation critical section.

For SQLite/simple contest project, a practical fix is a module-level lock:

import threading
_booking_create_lock = threading.Lock()

Then wrap conflict check, quota check, reference generation, insert, commit, stats/cache update carefully.

Better database-level approach would be BEGIN IMMEDIATE, but a Python lock is often enough for this hackathon container if it runs one app process.

10. Quota check is not concurrency-safe

File: app/routers/bookings.py
Lines: 55–71 and 103–117

Current quota logic checks count before inserting. Under concurrent requests, multiple requests can all see count < 3 and all insert.

That violates:

A member may hold at most 3 confirmed bookings in next 24 hours.
Must hold under concurrent requests.

Fix idea: same as above — protect booking creation with a lock/transaction.

11. Rate limiter is not concurrency-safe

File: app/services/ratelimit.py
Lines: 9–26

Current code uses a shared dictionary:

_buckets: dict[int, list[float]] = {}

But there is no lock. Concurrent requests can overwrite each other’s bucket state.

Also this artificial pause increases race chance:

time.sleep(0.1)

Fix idea:

import threading
_lock = threading.Lock()

def record_and_check(user_id: int) -> None:
    with _lock:
        now = time.time()
        bucket = _buckets.get(user_id, [])
        bucket = [t for t in bucket if t > now - _WINDOW_SECONDS]
        bucket.append(now)
        _buckets[user_id] = bucket
        if len(bucket) > _MAX_REQUESTS:
            raise AppError(429, "RATE_LIMITED", "Too many booking requests")

Rate limit must hold under concurrent requests.

12. Reference code generation is not concurrency-safe

File: app/services/reference.py
Lines: 8–21

Current code:

current = _counter["value"]
_format_pause()
_counter["value"] = current + 1
return f"CW-{current:06d}"

Because of the sleep, two requests can read the same counter value and generate the same reference code.

Also, the database model does not enforce uniqueness:

File: app/models.py
Line: 55

reference_code = Column(String, nullable=False, index=True)

It should be unique.

Fix idea:

reference_code = Column(String, nullable=False, unique=True, index=True)

And add a lock in reference.py:

import threading
_lock = threading.Lock()

def next_reference_code() -> str:
    with _lock:
        current = _counter["value"]
        _counter["value"] = current + 1
        return f"CW-{current:06d}"

The rule says every booking reference code must be unique, including concurrent creation.

13. Booking list pagination is wrong

File: app/routers/bookings.py
Lines: 134–140

Current code:

base.order_by(Booking.start_time.desc(), Booking.id.asc())
.offset(page * limit)
.limit(10)

Three bugs here:

Sorting is descending, but should be ascending.
Offset is page * limit, but should be (page - 1) * limit.
Limit is hardcoded to 10, ignoring the user's limit.

Fix idea:

items = (
    base.order_by(Booking.start_time.asc(), Booking.id.asc())
    .offset((page - 1) * limit)
    .limit(limit)
    .all()
)

The contract requires ascending start_time, ties by ascending id, no skipped/repeated items, and correct limit.

14. Member can read another member’s booking

File: app/routers/bookings.py
Lines: 156–160

Current query checks same organization:

.filter(Booking.id == booking_id, Room.org_id == user.org_id)

But it does not check ownership for members.

So member Bob can read member Alice’s booking if they are in the same org.

Expected:

Members may read only their own bookings.
Another member's booking ID → 404 BOOKING_NOT_FOUND.
Admins may read any booking in their org.

Fix idea:

After finding booking:

if user.role != "admin" and booking.user_id != user.id:
    raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")

The rule says members can only read/cancel their own bookings.

15. Single booking response has wrong start_time

File: app/routers/bookings.py
Line: 166

Current code:

response["start_time"] = iso_utc(booking.created_at)

This overwrites the actual booking start time with the booking creation time.

That is wrong.

Fix idea: remove this line completely.

serialize_booking() already correctly sets:

"start_time": iso_utc(booking.start_time)
16. Refund policy is wrong

File: app/routers/bookings.py
Lines: 198–206

Current code:

if notice_hours > 48:
    refund_percent = 100
elif notice >= timedelta(hours=24):
    refund_percent = 50
else:
    refund_percent = 50

Problems:

Exactly 48 hours should be 100%, but current code uses > 48.
Less than 24 hours should be 0%, but current code returns 50%.

Fix idea:

if notice >= timedelta(hours=48):
    refund_percent = 100
elif notice >= timedelta(hours=24):
    refund_percent = 50
else:
    refund_percent = 0

The required policy is 100% for notice ≥ 48h, 50% for 24–48h, and 0% for less than 24h.

17. Refund rounding is wrong

File: app/services/refunds.py
Lines: 14–17

Current code converts cents to dollars and uses int():

dollars = booking.price_cents / 100.0
refund_dollars = dollars * (percent / 100.0)
amount_cents = int(refund_dollars * 100)

This floors the value.

Example:

50% of 1001 cents = 500.5 cents
Expected = 501 cents
Current = 500 cents

Also, in cancel_booking, this line is not safe:

refund_amount_cents = round(booking.price_cents * (refund_percent / 100.0))

Python’s round() uses banker’s rounding, not half-up rounding.

Fix idea:

Use integer math:

amount_cents = (booking.price_cents * percent + 50) // 100

Then return the actual logged refund amount:

refund = log_refund(db, booking, refund_percent)
refund_amount_cents = refund.amount_cents

The contract specifically says half-cents round up.

18. Cancellation is not concurrency-safe

File: app/routers/bookings.py
Lines: 195–214

Current flow:

Check if booking is cancelled
Create refund log
Sleep
Set booking status cancelled
Commit

Two concurrent cancel requests can both pass the status check and both create refund logs.

That violates:

A cancelled booking has exactly one RefundLog entry.
Concurrent cancel requests must not create multiple refunds.

Fix idea:

Use a lock around cancellation or database transaction. Also add a DB uniqueness constraint:

booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True, index=True)

And make status update + refund log creation one atomic operation.

19. Usage report cache becomes stale after booking creation

File: app/routers/bookings.py
Lines: 120–122

After creating a booking, code invalidates availability:

cache.invalidate_availability(room.id, start.date().isoformat())

But it does not invalidate usage report cache.

So this can happen:

Admin opens usage report → cached
Member creates new booking
Admin opens usage report again → old cached result

But report must reflect current state immediately.

Fix idea:

cache.invalidate_report(user.org_id)

Add it after successful booking creation.

20. Availability cache becomes stale after cancellation

File: app/routers/bookings.py
Lines: 216–218

After cancellation, code invalidates report:

cache.invalidate_report(user.org_id)

But it does not invalidate room availability.

So a cancelled booking may still appear in /rooms/{id}/availability.

Fix idea:

cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())

Availability must reflect current state immediately.

21. Room stats are unreliable and concurrency-broken

File: app/services/stats.py
Lines: 8–30
File: app/routers/rooms.py
Lines: 103–115

Stats are stored only in memory:

_stats: dict[int, dict] = {}

Problems:

Stats reset if app restarts but database still has bookings.
Concurrent booking creation can lose updates.
Concurrent cancellation can lose updates.
Stats can disagree with real database bookings.

This violates:

GET /rooms/{id}/stats must always equal confirmed bookings and revenue from bookings.

Best fix idea: do not use in-memory stats. Calculate directly from database:

confirmed = (
    db.query(Booking)
    .filter(
        Booking.room_id == room.id,
        Booking.status == "confirmed",
    )
    .all()
)

return {
    "room_id": room.id,
    "total_confirmed_bookings": len(confirmed),
    "total_revenue_cents": sum(b.price_cents for b in confirmed),
}

The contract says room stats must always be consistent with bookings, including after concurrent activity.

22. Admin export can leak cross-organization data

File: app/services/export.py
Lines: 22–29 and 48–50

Current code:

def fetch_bookings_raw(db: Session, room_id: int) -> list[Booking]:
    return (
        db.query(Booking)
        .filter(Booking.room_id == room_id)
        .order_by(Booking.id.asc())
        .all()
    )

Then:

if include_all:
    if room_id is not None:
        rows = fetch_bookings_raw(db, room_id)

This is a serious multi-tenancy bug.

If admin from Org A passes room_id from Org B, the export can return Org B bookings.

Expected:

Users/admins may only act on data in their own organization.
Cross-org resource IDs behave as non-existent → 404.

Fix idea:

Always join Room and filter by Room.org_id == admin.org_id.

Also, if room_id is provided and does not belong to admin’s org, return:

404 ROOM_NOT_FOUND

Multi-tenancy applies to every code path, including exports.

23. Notification locks can deadlock the service

File: app/services/notifications.py
Lines: 24–35

Current code:

def notify_created(booking) -> None:
    with _email_lock:
        ...
        with _audit_lock:
            ...

def notify_cancelled(booking) -> None:
    with _audit_lock:
        ...
        with _email_lock:
            ...

This is a classic deadlock bug.

One request can hold _email_lock and wait for _audit_lock, while another holds _audit_lock and waits for _email_lock.

That violates the liveness rule:

No combination of concurrent valid requests may hang the service.

Fix idea: always acquire locks in the same order, or use one lock, or remove unnecessary sleeps/locks because email/audit are simulated.

Example:

def notify_created(booking) -> None:
    with _email_lock:
        _send_email("created", booking)
    with _audit_lock:
        _write_audit("created", booking)

def notify_cancelled(booking) -> None:
    with _email_lock:
        _send_email("cancelled", booking)
    with _audit_lock:
        _write_audit("cancelled", booking)
Smaller/non-grading issues
.idea/ files are included

Your zip includes PyCharm .idea/ files. Not a main API bug, but you should usually add this to .gitignore:

.idea/

This probably will not affect the grader, but it is cleaner.