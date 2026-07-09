# Bug: Incorrect Refund Notice Thresholds and Fallback

## Summary
The cancellation router verified the 48-hour notice threshold using `notice_hours > 48` (which failed for exactly 48 hours), and set the default fallback refund to 50% instead of 0% for cancellations made under 24 hours.

## Rule Violated
> **notice >= 48 hours &rarr; 100% refund; notice < 24 hours &rarr; 0% refund.**

## Severity
High

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Lines 207–214

## Original Code
```python
    now = datetime.utcnow()
    notice = booking.start_time - now
    notice_hours = int(notice.total_seconds() // 3600)
    if notice_hours > 48:
        refund_percent = 100
    elif notice >= timedelta(hours=24):
        refund_percent = 50
    else:
        refund_percent = 50
```

## Fixed Code
```python
    now = datetime.utcnow()
    notice = booking.start_time - now
    if notice >= timedelta(hours=48):
        refund_percent = 100
    elif notice >= timedelta(hours=24):
        refund_percent = 50
    else:
        refund_percent = 0
```

## Root Cause
Inequality operator flaw and incorrect fallback assignment.

## Fix Applied
Changed the logic to use exact `timedelta` comparisons and set the fallback percent to `0`.

## Why the Fix Works
Conforms directly to the specified notice intervals (ex: 48h gets 100%, and under 24h gets 0%).

## Concurrency Notes
N/A

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L329-L440).
