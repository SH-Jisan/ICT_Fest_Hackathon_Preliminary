# Bug: Flawed Offset Math Skips Page 1 Results

## Summary
The offset was calculated as `page * limit`, skipping the first page of results entirely (for page 1 and limit 10, offset evaluated to 10).

## Rule Violated
> **Pagination must use deterministic LIMIT and OFFSET calculations without skipping or repeating records.**

## Severity
Critical

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Line 147

## Original Code
```python
.offset(page * limit)
```

## Fixed Code
```python
.offset((page - 1) * limit)
```

## Root Cause
Incorrect page offset multiplier index.

## Fix Applied
Changed offset calculations to use `(page - 1) * limit`.

## Why the Fix Works
Ensures that page 1 starts at offset 0, retrieving results accurately.

## Concurrency Notes
N/A

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L654-L729).
