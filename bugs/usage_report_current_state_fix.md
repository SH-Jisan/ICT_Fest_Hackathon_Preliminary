# Bug: Stale Usage Report Cache on Booking Creation

## Summary
The administrator usage report endpoint returned stale cached data because the booking creation endpoint `POST /bookings` did not invalidate the report cache, causing newly created bookings to not be reflected in reports.

## Rule Violated
> **The report must always reflect the latest committed database state immediately. Recently created bookings, cancelled bookings, or updated bookings must immediately appear in the report.**

## Severity
High

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Line 131

## Original Code
```python
    stats.record_create(room.id, price_cents)
    cache.invalidate_availability(room.id, start.date().isoformat())
    notifications.notify_created(booking)
```

## Fixed Code
```python
    stats.record_create(room.id, price_cents)
    cache.invalidate_availability(room.id, start.date().isoformat())
    cache.invalidate_report(user.org_id)
    notifications.notify_created(booking)
```

## Root Cause
Missed cache invalidation triggers on booking creation.

## Fix Applied
Added `cache.invalidate_report(user.org_id)` invocation within `create_booking`.

## Why the Fix Works
Guarantees that any booking creation immediately invalidates the organization's cached usage reports, forcing the next report call to compute fresh statistics from the database.

## Concurrency Notes
N/A

## Tests Updated
Added `test_admin_usage_report_current_state` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L728-L792).
