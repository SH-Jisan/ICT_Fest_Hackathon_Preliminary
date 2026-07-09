# Bug: Booking start_time Past Grace Window Allowed

## Problem
The check `if start <= now - timedelta(seconds=300)` implemented an implicit 5-minute grace window in the past, allowing booking starts up to 5 minutes before the current time.

## Rule Violated
> **`start_time` must be strictly in the future at the request time. There is no grace window. `start_time == current_time` and `start_time < current_time` must be rejected.**

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 92–93

## Fix Applied
Removed the `- timedelta(seconds=300)` subtraction offset, changing the check to a direct comparison: `if start <= now`.

## Result
Any booking request whose start time is equal to or earlier than the current request time is strictly rejected with a `400 Bad Request`.
