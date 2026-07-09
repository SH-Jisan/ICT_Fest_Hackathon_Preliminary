# Bug: Nested Lock Circular Deadlock in Notifications

## Summary
The notification service acquired `_email_lock` and `_audit_lock` in nested, reverse order between `notify_created` (email -> audit) and `notify_cancelled` (audit -> email). Simultaneous creations and cancellations caused a circular wait, deadlocking the worker threads.

## Rule Violated
> **No combination of concurrent valid requests may hang the service, deadlock, livelock, block indefinitely, or prevent other requests from completing.**

## Severity
Critical

## Affected Files
* [app/services/notifications.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/notifications.py)

## Modified Line Numbers
* `notifications.py` : Lines 24–35

## Original Code
```python
def notify_created(booking) -> None:
    with _email_lock:
        _send_email("created", booking)
        with _audit_lock:
            _write_audit("created", booking)

def notify_cancelled(booking) -> None:
    with _audit_lock:
        _write_audit("cancelled", booking)
        with _email_lock:
            _send_email("cancelled", booking)
```

## Fixed Code
```python
def notify_created(booking) -> None:
    with _email_lock:
        _send_email("created", booking)
    with _audit_lock:
        _write_audit("created", booking)

def notify_cancelled(booking) -> None:
    with _audit_lock:
        _write_audit("cancelled", booking)
    with _email_lock:
        _send_email("cancelled", booking)
```

## Root Cause
Nested lock acquisitions in inconsistent/reverse orders creating circular wait states.

## Fix Applied
De-nested the lock acquisitions so they are acquired sequentially and independently.

## Why the Fix Works
Since no thread holds both locks simultaneously, a circular wait state is mathematically impossible, completely eliminating the deadlock condition.

## Concurrency & Performance Notes
Improves performance and throughput by reducing lock contention duration by half (from 0.22s to 0.1s and 0.12s independently).

## Tests Updated
Added `test_concurrent_notification_deadlock_safety` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L931-L985).
