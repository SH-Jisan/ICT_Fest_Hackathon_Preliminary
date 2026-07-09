# Bug: Potential Internal Server Crash on Non-Integer Token Subject

## Bug ID
BUG-018

## Summary
The application decoded the `sub` claim from the JWT (which is specified to be a user ID string) and parsed it directly using `int(payload["sub"])` without a `try/except ValueError` block. A malicious or malformed token carrying a non-integer `sub` value (like a username) would trigger an unhandled `ValueError` exception, crashing the request with a `500 Internal Server Error`.

## Severity
Medium

## Rule Violated
Error handling and API robustness. Malformed user identifiers must not trigger server crashes or leak internal traceback details.

## Affected Files
* [app/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/auth.py)
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 127–130
* `routers/auth.py` : Line 120

## Original Code
```python
# In app/auth.py:
user = db.query(User).filter(User.id == int(payload["sub"])).first()

# In app/routers/auth.py:
user = db.query(User).filter(User.id == int(data["sub"])).first()
```

## Fixed Code
```python
# In app/auth.py:
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise AppError(401, "UNAUTHORIZED", "Invalid token subject")
    user = db.query(User).filter(User.id == user_id).first()

# In app/routers/auth.py:
    try:
        user_id = int(data["sub"])
    except (ValueError, TypeError):
        raise AppError(401, "UNAUTHORIZED", "Invalid token subject")
    user = db.query(User).filter(User.id == user_id).first()
```

## Root Cause
Naive parsing of user ID strings without catching parsing exceptions.

## Fix Applied
Wrapped both conversion locations inside a `try/except (ValueError, TypeError)` block, raising a clean `AppError(401, "UNAUTHORIZED")` if parsing fails.

## Why the Fix Works
Prevents unhandled crashes and ensures that requests with invalid token subjects are rejected with a correct 401 response status.

## Regression Check
Re-ran pytest suite. All 17 tests passed successfully.

## Tests Added or Updated
Added `test_non_integer_token_subject` in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L982-L1004).
