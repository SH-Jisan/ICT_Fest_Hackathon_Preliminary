# Bug: In-Memory Room Stats Persistence and Consistency Failure

## Summary
The room statistics endpoint returned data stored inside an in-memory process-local dictionary. A server restart completely wiped all statistics, causing statistics to diverge from actual database states.

## Rule Violated
> **The returned statistics must always remain consistent with the actual bookings stored in the database. No cached, delayed, or eventually consistent values are allowed unless they are guaranteed to satisfy the specification immediately after every committed transaction.**

## Severity
Critical

## Affected Files
* [app/services/stats.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/stats.py)
* [app/routers/rooms.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/rooms.py)

## Modified Line Numbers
* `stats.py` : Lines 6–30
* `rooms.py` : Lines 109–115

## Original Code
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

## Fixed Code
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

## Root Cause
Room statistics were stored in a naive, transient in-memory dict structure instead of querying the database.

## Fix Applied
Re-implemented the `get` stats function to perform a database query using SQL aggregations (`COUNT` and `SUM` wrapped in `coalesce` to default to 0), and updated the endpoint to pass `db` and output correct keys (`confirmed_booking_count` and `total_price_cents`).

## Why the Fix Works
Forces statistics to always calculate in real-time from the database, guaranteeing absolute consistency even across restarts or multi-instance deployments.

## Performance & Concurrency Notes
Uses database indexes for fast query executions.

## Tests Updated
Added `test_room_stats_current_state` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L833-L901).
