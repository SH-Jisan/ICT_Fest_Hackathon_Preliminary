# Bug: Uncaught Database Integrity Exceptions on Concurrent Registrations

## Summary
Concurrent attempts to register identical organizations or usernames triggered database unique constraints, causing requests to crash with uncaught 500 errors.

## Rule Violated
> **The implementation must remain correct under concurrent registration requests, preventing duplicate organizations and usernames without raising internal server errors.**

## Severity
High

## Affected Files
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 24–75

## Original Code
```python
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Raw queries and database updates without error handling
```

## Fixed Code
```python
    try:
        ...
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handle concurrent registration collisions
        org = db.query(Organization).filter(Organization.name == org_name).first()
        if org is not None:
            existing = (
                db.query(User)
                .filter(User.org_id == org.id, User.username == username)
                .first()
            )
            if existing is not None:
                raise AppError(409, "USERNAME_TAKEN", "Username taken")
            
            try:
                user = User(
                    org_id=org.id,
                    username=username,
                    hashed_password=hash_password(payload.password),
                    role="member",
                )
                db.add(user)
                db.commit()
            except IntegrityError:
                db.rollback()
                raise AppError(409, "USERNAME_TAKEN", "Username taken")
        else:
            raise AppError(409, "USERNAME_TAKEN", "Username taken")
```

## Root Cause
No database unique constraint conflict catching in application routers.

## Fix Applied
Wrapped registration logic in a `try/except IntegrityError` block. If organization name collision occurs, the database rolls back, loads the existing organization, and registers the caller as a member (Case 2 fallback). If username collision occurs, returns `409 USERNAME_TAKEN`.

## Why the Fix Works
Prevents 500 errors and resolves concurrency races safely using transaction rollbacks and re-checks.

## Concurrency & Security Notes
Utilizes SQLAlchemy `IntegrityError` to safely resolve concurrent race conditions.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L891-L935).
