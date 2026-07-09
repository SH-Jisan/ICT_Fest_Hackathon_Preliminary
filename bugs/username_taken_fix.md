# Bug: Success Response on Duplicate Username Registration

## Summary
The registration endpoint returned a successful response containing the user's details when an existing username was submitted, bypassing uniqueness protections.

## Rule Violated
> **Attempting to register a duplicate username within the same organization must return HTTP 409 Conflict with Error Code: USERNAME_TAKEN.**

## Severity
Critical

## Affected Files
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 39–46

## Original Code
```python
    existing = (
        db.query(User)
        .filter(User.org_id == org.id, User.username == payload.username)
        .first()
    )
    if existing is not None:
        return {
            "user_id": existing.id,
            "org_id": org.id,
            "username": existing.username,
            "role": existing.role,
        }
```

## Fixed Code
```python
        existing = (
            db.query(User)
            .filter(User.org_id == org.id, User.username == username)
            .first()
        )
        if existing is not None:
            raise AppError(409, "USERNAME_TAKEN", "Username taken")
```

## Root Cause
Lacked duplicate conflict rejection raising.

## Fix Applied
Changed the block to raise `AppError(409, "USERNAME_TAKEN", "Username taken")` if a duplicate username matches the organization id.

## Why the Fix Works
Enforces correct HTTP status 409 and code `USERNAME_TAKEN` to prevent registration account hijacking.

## Concurrency Notes
N/A

## Tests Updated
Added `test_user_registration_compliance` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L891-L935).
