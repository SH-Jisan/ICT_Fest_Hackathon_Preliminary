# Bug: Incorrect Booking Sorting Order

## Summary
The bookings query sorted results using descending start times (`start_time.desc()`), while the specification required ascending start times (`start_time ASC`) with ascending ID tie-breakers (`id ASC`).

## Rule Violated
> **Bookings must always be sorted using: ORDER BY start_time ASC, id ASC.**

## Severity
High

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Line 146

## Original Code
```python
base.order_by(Booking.start_time.desc(), Booking.id.asc())
```

## Fixed Code
```python
base.order_by(Booking.start_time.asc(), Booking.id.asc())
```

## Root Cause
Incorrect sorting direction used in ORM.

## Fix Applied
Updated sorting inside `list_bookings` query to use `Booking.start_time.asc()`.

## Why the Fix Works
Enforces deterministic chronological ascending list results as required.

## Concurrency Notes
N/A

## Tests Updated
Added `test_booking_pagination_and_ordering` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L654-L729).
