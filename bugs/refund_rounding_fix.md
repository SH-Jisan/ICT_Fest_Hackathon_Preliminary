# Bug: Refund Cents Rounding Strategy Mismatch

## Summary
The cancellation router used Python's default banker's rounding, while the database ledger service truncated decimals using `int()`, creating mismatches in stored values vs API responses.

## Rule Violated
> **Refund amounts must be rounded to the nearest cent. If the calculation results in exactly half a cent, it must round up. The refund amount returned in the cancellation response must exactly equal the value stored in the RefundLog.**

## Severity
High

## Affected Files
* [app/timeutils.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/timeutils.py)
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)
* [app/services/refunds.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/refunds.py)

## Modified Line Numbers
* `timeutils.py` : Lines 20–25
* `bookings.py` : Lines 216
* `refunds.py` : Lines 12–15

## Original Code
```python
# In bookings.py:
refund_amount_cents = round(booking.price_cents * (refund_percent / 100.0))

# In refunds.py:
dollars = booking.price_cents / 100.0
refund_dollars = dollars * (percent / 100.0)
amount_cents = int(refund_dollars * 100)
```

## Fixed Code
```python
# In timeutils.py:
def round_half_up(value: float) -> int:
    return int(value + 0.5)

# In bookings.py:
refund_amount_cents = round_half_up(booking.price_cents * (refund_percent / 100.0))

# In refunds.py:
amount_cents = round_half_up(booking.price_cents * (percent / 100.0))
```

## Root Cause
Different rounding approaches used across modules.

## Fix Applied
Implemented a shared `round_half_up` function and utilized it in both modules.

## Why the Fix Works
Guarantees consistent rounding behavior where half-cents are always rounded up to the next integer.

## Concurrency Notes
N/A

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L329-L440).
