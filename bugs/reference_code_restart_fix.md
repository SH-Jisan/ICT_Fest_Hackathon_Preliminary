# Bug: Reference Code Volatility on Restart

## Summary
The booking reference code generator stored the counter in volatile in-memory dictionary `_counter = {"value": 1000}`. If the application server restarted, the counter was reset to 1000, causing it to output duplicate reference codes that already exist in the database, resulting in database crashes (IntegrityError).

## Rule Violated
> **Every booking must have a reference_code that is unique... Persistent in the database.**

## Severity
High

## Affected Files
* [app/services/reference.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/services/reference.py)

## Modified Line Numbers
* `reference.py` : Lines 5–27

## Original Code
```python
_counter = {"value": 1000}

def next_reference_code() -> str:
    current = _counter["value"]
    _format_pause()
    _counter["value"] = current + 1
    return f"CW-{current:06d}"
```

## Fixed Code
```python
_counter = {"value": 1000}
_reference_lock = threading.Lock()

def next_reference_code(db: Session) -> str:
    with _reference_lock:
        if _counter["value"] == 1000:
            from ..models import Booking
            max_ref = db.query(Booking.reference_code).order_by(Booking.reference_code.desc()).first()
            if max_ref and max_ref[0]:
                try:
                    code_num = int(max_ref[0].split("-")[1])
                    _counter["value"] = max(code_num + 1, _counter["value"])
                except (IndexError, ValueError):
                    pass

        while True:
            current = _counter["value"]
            _format_pause()
            _counter["value"] = current + 1
            code = f"CW-{current:06d}"
            
            # Check collisions...
```

## Root Cause
Volatile state variable reset on application load.

## Fix Applied
Added database seeding logic on first generator execution: queries the highest reference code prefix from the database and sets the monotonic counter starting point above it.

## Why the Fix Works
Prevents counter reset issues upon application restarts by dynamically seeding from persisted database state.

## Concurrency Notes
N/A

## Tests Updated
Added `test_reference_code_seeding_and_collision` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L438-L491).
