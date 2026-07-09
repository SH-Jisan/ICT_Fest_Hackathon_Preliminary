# Bug: Flawed Access Token Revocation Check

## Summary
The system checked if a user's `sub` (User ID string) existed inside `_revoked_tokens` to detect logged-out tokens. Since `_revoked_tokens` stores token `jti` UUIDs, the revocation check always evaluated to False, letting logged-out access tokens bypass checks.

## Rule Violated
> **Logout must immediately invalidate the presented access token. Subsequent requests using that token must return 401 Unauthorized.**

## Severity
Critical

## Affected Files
* [app/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/auth.py)

## Modified Line Numbers
* `auth.py` : Lines 105–120

## Original Code
```python
def revoke_access_token(payload: dict) -> None:
    _revoked_tokens.add(payload["jti"])

def get_token_payload(request: Request) -> dict:
    ...
    if payload.get("sub") in _revoked_tokens:
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
```

## Fixed Code
```python
def revoke_access_token(payload: dict) -> None:
    check_and_revoke_token(payload.get("jti"))

def get_token_payload(request: Request) -> dict:
    ...
    if is_token_revoked(payload.get("jti")):
        raise AppError(401, "UNAUTHORIZED", "Token has been revoked")
```

## Root Cause
The validation checked `sub` instead of `jti`.

## Fix Applied
Updated the verification logic to query `is_token_revoked` using `jti`, and synchronized updates under a global thread lock.

## Why the Fix Works
Conforms directly to mapping tokens by unique JTI claims, ensuring logged-out access tokens fail validation instantly.

## Concurrency Notes
N/A

## Tests Updated
Added `test_auth_logout_and_refresh_rotation` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L492-L545).
