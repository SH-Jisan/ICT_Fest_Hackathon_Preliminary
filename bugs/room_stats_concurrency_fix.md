# Bug: Room Stats Lost Updates Concurrency Race Condition

## Summary
The statistics update functions fetched state, paused artificially, and overwrote process memory, causing concurrent bookings to collision-overwrite each other's increments.

## Rule Violated
> **The implementation must remain correct under concurrent requests. Concurrent booking creation, confirmation, or cancellation must never produce logically incorrect aggregation.**

## Severity
Critical

## Affected Files
* [app/services/stats.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/stats.py)

## Modified Line Numbers
* `stats.py` : Lines 6–30

## Original Code
```python
def record_create(room_id: int, price_cents: int) -> None:
    current = _stats.get(room_id, {"count": 0, "revenue": 0})
    count, revenue = current["count"], current["revenue"]
    _aggregate_pause()
    _stats[room_id] = {"count": count + 1, "revenue": revenue + price_cents}
```

## Fixed Code
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

## Root Cause
In-memory counters modified without concurrency locks and with sleep delays.

## Fix Applied
Changed the backend design to fetch aggregates directly from the database using SQL queries, resolving concurrent race conditions entirely by relying on database transaction safety.

## Why the Fix Works
Relying on database engines for aggregation ensures that stats updates are safe under concurrent transactions.

## Concurrency Notes
Ensured that concurrent request safety inherits directly from database engine ACID transactions.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L833-L901).
