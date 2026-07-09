# Bug: Concurrent Booking Race Condition

## Problem
The room booking creation flow did not lock database records or synchronize validations, allowing concurrent requests to create overlapping bookings for the same room.

## Rule Violated
> **Two simultaneous requests must never create overlapping confirmed bookings for the same room. The booking creation process must be concurrency-safe.**

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 26, 108–127

## Root Cause
The validation checks (`_has_conflict` and `_check_quota`) and database insert were executed asynchronously without locks or database row-level locking. Under concurrent request spikes, multiple threads could read the same database state and write overlapping confirmed bookings.

## Fix Applied
Defined a global `_booking_lock = threading.Lock()` and wrapped the validation checks (`_has_conflict` and `_check_quota`), reference generation, and database insert/commit operations inside a `with _booking_lock:` synchronized block.

## Result
Only one thread can check and write booking reservations at a time, completely preventing concurrent race conditions.

## Concurrency Notes
A thread lock in Python's multi-threaded ASGI worker environment guarantees thread safety. This prevents race conditions and handles SQLite's single-process model safely without causing database locks.

## Tests Updated
Added conflict overlap tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L110-L203).
