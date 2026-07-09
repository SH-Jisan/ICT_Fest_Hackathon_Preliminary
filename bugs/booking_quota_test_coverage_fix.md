# Bug: Missing Booking Quota Test Coverage

## Summary
The integration test suite did not contain any checks to verify that booking quota validations, limits, boundaries, or exclusions (like bookings outside the 24-hour window) were enforced correctly.

## Rule Violated
> **A member may hold at most 3 confirmed bookings whose start_time falls within (now, now + 24 hours].** (Implicitly: Business rules must be adequately validated via integration tests).

## Severity
Low

## Affected Files
* [tests/test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py)

## Modified Line Numbers
* `test_smoke.py` : Lines 223–296

## Original Code
No test code existed for checking user booking quota limits.

## Fixed Code
Added a new integration test [test_booking_quota_limits](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L223-L296):
```python
def test_booking_quota_limits():
    # Setup organization and user...
    # Create 3 bookings in next 24h:
    # res_1, res_2, res_3 -> assert status_code == 201
    
    # 4th booking in window:
    # assert res_4.status_code == 409 and res_4.json()["code"] == "QUOTA_EXCEEDED"
    
    # 5th booking outside window:
    # assert res_5.status_code == 201
```

## Root Cause
Insufficient test coverage for boundary validations and failure code execution paths.

## Fix Applied
Appended the `test_booking_quota_limits` function to `tests/test_smoke.py` to cover all limits, boundary dates, HTTP 409 responses, and success paths outside the window.

## Why the Fix Works
It automatically asserts and validates that the booking quota rules are strictly enforced and prevents regressions during future updates.

## Tests Updated
* [tests/test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py)
