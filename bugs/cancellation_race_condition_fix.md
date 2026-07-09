# Bug: Concurrent Cancellation State Race Condition

## Bug ID
BUG-022

## Summary
The cancellation endpoint queried the booking, checked if it was already cancelled, created a refund entry, slept during a simulated settlement pause, updated the booking's status to `cancelled`, and committed. Under concurrent cancellation requests for the same booking ID, both threads could retrieve the initial `confirmed` state of the booking before the status update was committed, leading to duplicate refund logs.

## Severity
High

## Rule Violated
A cancelled booking must create exactly one RefundLog, and concurrent cancel requests for the same booking must not create multiple refund logs.

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)
* [app/services/refunds.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/refunds.py)

## Modified Line Numbers
* `bookings.py` : Lines 196–228
* `refunds.py` : Lines 15–24

## Original Code
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

## Fixed Code
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

## Root Cause
Querying the resource status and validating it outside the synchronization lock boundaries, allowing concurrent threads to proceed past the validation check.

## Fix Applied
Moved the database query, permission verification, state validation check, `log_refund` invocation, and the single final `db.commit()` inside the synchronized `with _booking_lock:` thread block. Refactored `log_refund` to perform `db.flush()` instead of commits to guarantee atomic database updates.

## Why the Fix Works
Forces all concurrent threads to serialize execution. The second thread will wait for the first to release the lock, at which point it queries the updated `cancelled` status from the database and immediately raises `409 ALREADY_CANCELLED` without executing any duplicate refund logic.

## Regression Check
Re-ran pytest integration tests. All 17 tests passed successfully.

## Tests Added or Updated
N/A (Exhaustive integration tests assert concurrent cancellation safety).
