# Bug: Zero/Negative Booking Durations Allowed

## Problem
The validation logic only verified if `duration_hours > 8`, neglecting to enforce the minimum duration limit (`duration_hours < 1`). As a result, users could submit reservations with negative or zero durations.

## Rule Violated
> **Minimum duration: 1 hour. Zero-hour and negative durations are not allowed.**

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 94–95

## Fix Applied
Changed the assertion check from `duration_hours > MAX_DURATION_HOURS` to `not (1 <= duration_hours <= MAX_DURATION_HOURS)`.

## Result
Any duration that evaluates to less than 1 hour or greater than 8 hours (including zero-hour and negative durations) is now correctly rejected with a `400 Bad Request` and error code `INVALID_BOOKING_WINDOW`.
