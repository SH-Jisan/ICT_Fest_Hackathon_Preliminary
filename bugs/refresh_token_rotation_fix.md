# Bug: Missing Refresh Token Rotation and Replay Protection

## Summary
The refresh endpoint decoded tokens and returned new credentials without revoking or marking the old refresh token as used. Users could reuse the same refresh token indefinitely to generate credentials.

## Rule Violated
> **Refresh tokens are single-use. Refreshing a token must immediately invalidate the presented refresh token. If the old refresh token is used again, the API must return 401 Unauthorized.**

## Severity
Critical

## Affected Files
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)
* [app/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 23–45
* `routers/auth.py` : Lines 81–96

## Original Code
```python
# In routers/auth.py:
@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Wrong token type")
    user = db.query(User).filter(User.id == int(data["sub"])).first()
    ...
```

## Fixed Code
```python
# In auth.py:
def check_and_revoke_token(jti: str) -> bool:
    if not jti:
        return False
    with _revocation_lock:
        if jti in _revoked_tokens:
            return False
        _revoked_tokens.add(jti)
        return True

# In routers/auth.py:
@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Wrong token type")
    
    if not check_and_revoke_token(data.get("jti")):
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
    ...
```

## Root Cause
No revocation tracking for refresh tokens.

## Fix Applied
Implemented a synchronized, atomic `check_and_revoke_token` block that revokes the token `jti` on first use and rejects subsequent reuse attempts.

## Why the Fix Works
Guarantees refresh tokens are strictly single-use and protects against concurrent replay attempts.

## Concurrency Notes
Uses `_revocation_lock = threading.Lock()` to serialize checks and revocations.

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L492-L545).
