# Bug: Back-to-Back Booking Incorrectly Rejected

## Problem
The booking overlap validation checked boundaries using `<=` (less-than-or-equal) comparisons. This blocked back-to-back room bookings (where one booking ends exactly when the next begins) because the boundary match was flagged as a conflict.

## Rule Violated
> **Back-to-back bookings are allowed. `existing.end == new.start` is NOT an overlap.**

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 49–51

## Root Cause
The loop inside `_has_conflict` checked: `if b.start_time <= end and start <= b.end_time: return True`. Because of the equal condition (`<=`), any slot ending exactly at the start time of the next booking triggered a conflict.

## Fix Applied
Changed the logic to use strict `<` comparison operators: `if b.start_time < end and start < b.end_time: return True`.

## Result
Back-to-back bookings (e.g. `10:00 -> 11:00` and `11:00 -> 12:00`) are now accepted, while overlapping slots are strictly rejected.
