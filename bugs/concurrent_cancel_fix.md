# Bug: Concurrent Booking Cancellation Race Condition

## Summary
The cancellation route validated status and executed updates without synchronization, allowing concurrent requests to bypass status checks and write duplicate `RefundLog` entries.

## Rule Violated
> **If two cancellation requests for the same booking occur simultaneously, only one request may succeed... The losing request must return HTTP 409 Conflict ALREADY_CANCELLED.**

## Severity
Critical

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Lines 204–224

## Original Code
```python
    if booking.status == "cancelled":
        raise AppError(409, "ALREADY_CANCELLED", "Booking already cancelled")
    ...
    log_refund(db, booking, refund_percent)
    booking.status = "cancelled"
    db.commit()
```

## Fixed Code
```python
    with _booking_lock:
        if booking.status == "cancelled":
            raise AppError(409, "ALREADY_CANCELLED", "Booking already cancelled")
        ...
        log_refund(db, booking, refund_percent)
        booking.status = "cancelled"
        db.commit()
```

## Root Cause
State checking and writing were executed without thread synchronization.

## Fix Applied
Wrapped validations and commits under `_booking_lock`.

## Why the Fix Works
Forces sequential evaluation of cancellation status and ledger inserts.

## Concurrency Notes
Uses `threading.Lock` to guarantee atomic process-level status checks.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L329-L440).
