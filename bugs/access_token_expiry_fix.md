# Bug: Access Token Expiry Mismatch

## Bug ID
AUTH-001

## Summary
The access token expiration lifetime was erroneously calculated as 900 minutes (15 hours) instead of 900 seconds (15 minutes), violating the 15-minute token expiry security specifications.

## Severity
High

## Rule Violated
Access tokens must expire in exactly 900 seconds (15 minutes).

## Affected Files
* [app/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/auth.py)

## Modified Line Numbers
* `auth.py` : Line 71

## Original Code
```python
    lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
```

## Fixed Code
```python
    lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

## Root Cause
The formula multiplied the 15-minute constant by 60 while inside the `minutes` parameter of `timedelta()`, resulting in 900 minutes.

## Fix Applied
Removed the `* 60` multiplier to correctly evaluate the duration to exactly 15 minutes (900 seconds).

## Why the Fix Works
Now `lifetime.total_seconds()` evaluates to exactly `900`, yielding the correct token expiration design.

## Regression Check
Re-ran pytest integration tests. All 16 tests passed.

## Tests Added or Updated
N/A
