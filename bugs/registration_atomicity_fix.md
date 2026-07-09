# Bug: Non-Atomic User Registration Commits

## Summary
The user registration endpoint committed organization creation to the database *before* executing the user insert query, resulting in orphan organization rows if user insertion failed.

## Rule Violated
> **Registration must execute inside a single database transaction. The database must never be left in a partially completed state.**

## Severity
High

## Affected Files
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 30–35

## Original Code
```python
    if org is None:
        org = Organization(name=payload.org_name)
        db.add(org)
        db.commit()
        db.refresh(org)
```

## Fixed Code
```python
        if org is None:
            org = Organization(name=org_name)
            db.add(org)
            db.flush()
        ...
        db.add(user)
        db.commit()
```

## Root Cause
Intermediate database commits in the middle of a multi-step logical transaction.

## Fix Applied
Removed the intermediary `db.commit()` on organization creation, using `db.flush()` instead to allocate IDs, committing both additions atomically at the end.

## Why the Fix Works
Ensures that if user creation fails, the transaction rolls back, reverting organization additions.

## Concurrency & Security Notes
Enforces database-level transaction rollbacks.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L891-L935).
