# Bug: Cross-Organization CSV Export Data Leak

## Summary
The admin export service did not filter bookings by organization boundaries when a specific room ID was requested with `include_all=True`. It retrieved competitor booking rows from other organizations without verification.

## Rule Violated
> **Every authenticated user, including administrators, may only access resources that belong to their own organization. No repository or service method may fetch a resource by ID alone if that resource belongs to an organization.**

## Severity
Critical

## Affected Files
* [app/services/export.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/export.py)

## Modified Line Numbers
* `export.py` : Lines 22–30, 50–51

## Original Code
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

## Fixed Code
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

## Root Cause
The database query filtered only on `room_id`, missing organization bounds check.

## Fix Applied
Modified `fetch_bookings_raw` to accept `org_id` and filter on `Room.org_id == org_id` via a SQL join.

## Why the Fix Works
Prevents any cross-organization SQL reads inside database-level queries.

## Concurrency Notes
N/A

## Tests Updated
Added `test_admin_export_multi_tenancy` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L539-L592).
