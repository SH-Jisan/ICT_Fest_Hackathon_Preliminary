# CoWork API — Registration Compliance Audit

This document presents a comprehensive audit of the user registration functionality within the CoWork API codebase, cross-checking role assignments, username uniqueness enforcement, organization matching policies, transaction atomicity, and concurrent safety.

---

## 1. Compliance Audit of Requirements

### A. Unknown Organization
* **Audit Result**: Compliant.
* **Details**: Creates a new organization, associates the registering user, and assigns the `admin` role.

### B. Existing Organization
* **Audit Result**: Compliant.
* **Details**: Joins the existing organization and assigns the `member` role.

### C. Username Uniqueness
* **Audit Result**: **Non-Compliant (Critical Violation)**.
* **Details**:
  - Inside [auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py#L38-L44), if the username already exists in the organization, it returns a success response containing the user's details.
  - The specification strictly requires returning `HTTP 409 Conflict` and `USERNAME_TAKEN`.

### D. Organization Name Matching
* **Audit Result**: Compliant.
* **Details**: Matches case-sensitively via SQLite defaults. String comparison is case-sensitive.

### E. Transaction Atomicity
* **Audit Result**: **Non-Compliant (High Violation)**.
* **Details**:
  - The registration endpoint commits the organization creation (`db.commit()`) *before* executing the user creation query.
  - If user insertion fails, the organization is left orphan/partially created, violating transaction atomicity.

### F. Concurrent Registration Safety
* **Audit Result**: **Non-Compliant (High Violation)**.
* **Details**:
  - Concurrent registration attempts for the same organization name or duplicate usernames will trigger database `IntegrityError` constraints.
  - Because these database integrity exceptions are not caught or handled, they crash the requests, returning `500 Internal Server Error` instead of a graceful rollback and correct conflict error.

### G. Role/Membership Spoofing
* **Audit Result**: Compliant.
* **Details**: The `RegisterRequest` schema does not accept a role field; the server determines all roles.

### H. Test Coverage
* **Audit Result**: Non-Compliant.
* **Details**: Integration tests do not assert duplicate username rejection behavior or concurrent integrity rollbacks.

---

## 2. Line-by-Line Findings

### REGISTER-001: Success Response on Duplicate Username
* **File Path**: `app/routers/auth.py`
* **File Name**: `auth.py`
* **Function**: `register`
* **Line Number(s)**: 38–44
* **Severity**: Critical
* **Rule Violated**: "Attempting to register a duplicate username within the same organization must return: HTTP 409 Conflict, Error Code: USERNAME_TAKEN."
* **Current Implementation**:
```python
    if existing is not None:
        return {
            "user_id": existing.id,
            "org_id": org.id,
            "username": existing.username,
            "role": existing.role,
        }
```
* **Why it is Incorrect**: Returns `201 Created` / `200 OK` success status and leaks user metadata instead of throwing a 409 error.
* **Potential Impact**: Security bypass allowing users to inspect or duplicate existing accounts.
* **Recommended Fix**: Raise an `AppError(409, "USERNAME_TAKEN", "Username taken")` if `existing is not None`.

---

### REGISTER-002: Intermediary Transaction Commits (Non-Atomic)
* **File Path**: `app/routers/auth.py`
* **File Name**: `auth.py`
* **Function**: `register`
* **Line Number(s)**: 30
* **Severity**: High
* **Rule Violated**: "Registration must be atomic. Unknown organization registration must never leave the database in a partially created state."
* **Current Implementation**:
```python
    if org is None:
        org = Organization(name=payload.org_name)
        db.add(org)
        db.commit()
```
* **Why it is Incorrect**: Commits the organization before the user creation is even attempted.
* **Potential Impact**: Orphaned organization rows on user registration failure.
* **Recommended Fix**: Remove the intermediary commit and execute one atomic transaction for both additions.

---

### REGISTER-003: Uncaught Database Integrity Exceptions on Concurrency
* **File Path**: `app/routers/auth.py`
* **File Name**: `auth.py`
* **Function**: `register`
* **Line Number(s)**: 24–60
* **Severity**: High
* **Rule Violated**: "The implementation must remain correct under concurrent requests... The implementation must prevent duplicate organizations, duplicate usernames... race conditions."
* **Current Implementation**:
Inserts database records without error catching.
* **Why it is Incorrect**: Concurrent inserts violate unique constraints, raising database exceptions that default to 500 Internal Server Errors.
* **Potential Impact**: Server crashes and raw database exception exposure under high load.
* **Recommended Fix**: Wrap registration within a `try/except IntegrityError` block. Rollback on exception, and if organization exists, retry with Case 2 logic. If username exists, return `409 USERNAME_TAKEN`.

---

## 3. Compliance Summary

* **Overall Registration Compliance Score**: **50%**
* **Organization Creation Compliance**: 100%
* **Role Assignment Compliance**: 100%
* **Username Uniqueness Compliance**: 0%
* **Organization Matching Compliance**: 80%
* **Transaction Safety Score**: 0%
* **Concurrency Safety Score**: 0%
* **Security Score**: 100%
* **Test Coverage Score**: 20%

---

## 4. Final Conclusion

### 1. Does registering with a new organization create both the organization and an admin user?
Yes.

### 2. Does registering with an existing organization create a member without creating another organization?
Yes.

### 3. Are usernames unique only within the same organization?
Yes.

### 4. Does a duplicate username correctly return HTTP 409 Conflict with `USERNAME_TAKEN`?
No, it returns success data.

### 5. Is registration atomic?
No, it commits organization creation prematurely.

### 6. Is the implementation safe under concurrent registration requests?
No, it triggers unhandled 500 errors on unique constraint violations.

### 7. Can clients manipulate organization membership or assigned roles?
No.

### 8. Which files violate the specification?
* [app/routers/auth.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/auth.py)

### 9. Which issues are the highest priority to fix?
* **REGISTER-001** (Success response on duplicate username).
* **REGISTER-002** (Non-atomic registration commits).
* **REGISTER-003** (Unhandled concurrency integrity crashes).
