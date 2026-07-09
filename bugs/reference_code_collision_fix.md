# Bug: Missing Reference Code Collision Recovery

## Summary
The system did not check if a generated reference code existed before writing it to the database, causing raw IntegrityError database exceptions to crash the application on collisions.

## Rule Violated
> **If a generated reference code already exists, the system must safely generate a new unique code before the booking is committed.**

## Severity
Critical

## Affected Files
* [app/services/reference.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/reference.py)
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `reference.py` : Lines 28–35
* `bookings.py` : Line 121

## Original Code
```python
# In bookings.py:
reference_code=reference.next_reference_code()
```

## Fixed Code
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

## Root Cause
No validation/recovery retry loop.

## Fix Applied
Implemented a check-and-retry database loop inside `next_reference_code`.

## Why the Fix Works
Ensures returned reference codes are not already recorded in the database, resolving collisions transparently.

## Concurrency Notes
Uses `_reference_lock = threading.Lock()` to serialize checks and prevent concurrency race conditions.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L438-L491).
