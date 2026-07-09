# Bug: Missing booking end_time Sequence Validation

## Problem
The application lacked an explicit logical validation rule asserting that the booking's end time is after its start time, relying instead on duration checks which could be bypassed via negative duration integers.

## Rule Violated
> **`end_time` must be strictly after `start_time`.**

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 89–90

## Fix Applied
Added an explicit validation check: `if end <= start: raise AppError(400, "INVALID_BOOKING_WINDOW", "end_time must be strictly after start_time")`.

## Result
Any booking request where the end time is less than or equal to the start time is rejected with a `400 Bad Request` and error code `INVALID_BOOKING_WINDOW`.
