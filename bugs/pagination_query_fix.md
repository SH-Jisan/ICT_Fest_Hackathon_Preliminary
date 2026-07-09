# Bug: Hardcoded Query Limit Ignores User Input

## Summary
The bookings listing query hardcoded `.limit(10)`, completely ignoring the user-supplied `limit` query parameters.

## Rule Violated
> **The endpoint must support limit query parameters (default 10, max 100).**

## Severity
Critical

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Line 148

## Original Code
```python
.limit(10)
```

## Fixed Code
```python
.limit(limit)
```

## Root Cause
Hardcoded pagination parameter inside query execution.

## Fix Applied
Replaced the hardcoded constant with the validated `limit` variable.

## Why the Fix Works
Dynamically applies the client's page size request.

## Concurrency Notes
N/A

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L654-L729).
