# Bug: Rate Limiter Race Condition

## Summary
The rate limiter read and modified the volatile user request bucket without synchronization, allowing concurrent requests to bypass the limit.

## Rule Violated
> **The implementation must remain correct under concurrent requests.**

## Severity
Critical

## Affected Files
* [app/services/ratelimit.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/ratelimit.py)

## Modified Line Numbers
* `ratelimit.py` : Lines 10, 20–28

## Original Code
```python
def record_and_check(user_id: int) -> None:
    now = time.time()
    bucket = _buckets.get(user_id, [])
    bucket = [t for t in bucket if t > now - _WINDOW_SECONDS]
    _settle_pause()
    bucket.append(now)
    _buckets[user_id] = bucket
    if len(bucket) > _MAX_REQUESTS:
        raise AppError(429, "RATE_LIMITED", "Too many booking requests")
```

## Fixed Code
```python
_limiter_lock = threading.Lock()

def record_and_check(user_id: int) -> None:
    with _limiter_lock:
        now = time.time()
        bucket = _buckets.get(user_id, [])
        bucket = [t for t in bucket if t > now - _WINDOW_SECONDS]
        _settle_pause()
        bucket.append(now)
        _buckets[user_id] = bucket
        if len(bucket) > _MAX_REQUESTS:
            raise AppError(429, "RATE_LIMITED", "Too many booking requests")
```

## Root Cause
Shared resource updates were not thread-safe.

## Fix Applied
Synchronized state modifications using a global `threading.Lock`.

## Why the Fix Works
It serializes bucket updates, ensuring accurate rolling window checks under concurrent loads.

## Concurrency Notes
Uses `threading.Lock` to guarantee process-level thread safety in ASGI environments.

## Tests Updated
Added `test_rate_limiting` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L296-L329).
