# CoWork API — Data Model Compliance Audit

This document presents a comprehensive data model compliance audit of the CoWork API codebase, cross-checking the database schema, ORM layer, relationships, API endpoints, business logic, validation, and integrity against the required data model specifications.

---

## 1. Compliance Audit per Data Model

### A. Organization

#### 1. Database Schema
* **Table Exists**: Yes, named `organizations` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L17-L21).
* **Required Fields Present**: `id` (Integer, Primary Key), `name` (String, Unique, Index).
* **Missing Required Fields**: **`created_at`** is completely missing from the database schema.
* **Unexpected Fields**: None.
* **Appropriate Types**: Yes.
* **Constraints**: `name` has a Unique constraint and an index. Primary key `id` is auto-incremented.

#### 2. ORM / Model Layer
* **Model Exists**: Yes, `Organization` class in `app/models.py`.
* **Field Names Match**: `id` and `name` match. **`created_at`** is missing.
* **Types Match**: Yes.
* **Relationships**: No relationships (e.g. to `User` or `Room`) are defined as SQLAlchemy attributes.
* **Cascade Rules**: No ORM-level cascade rules are defined.

#### 3. API Layer Support
* **Create**: Partially supported through `POST /auth/register` (creates organization if it does not exist).
* **Read / Update / Delete**: Completely missing. There are no endpoints to list, retrieve, update, or delete organizations.

#### 4. Business Logic
* **Organization Isolation**: Handled via `org_id` filters on rooms and bookings, but there is no direct organization configuration endpoint.

---

### B. User

#### 1. Database Schema
* **Table Exists**: Yes, named `users` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L24-L33).
* **Required Fields Present**: `id` (Integer, PK), `org_id` (Integer, FK to `organizations.id`), `username` (String), `hashed_password` (String), `role` (String), `created_at` (DateTime).
* **Missing Required Fields**: None.
* **Unexpected Fields**: None.
* **Appropriate Types**: Yes, SQLite native mapping is correct.
* **Constraints**: Unique constraint on `(org_id, username)` named `uq_user_org_username` is present. Primary key `id` is correct. Foreign key `org_id` is defined.

#### 2. ORM / Model Layer
* **Model Exists**: Yes, `User` class in `app/models.py`.
* **Field Names Match**: Yes.
* **Types Match**: Yes.
* **Relationships**: No ORM-level relationships to `Organization` or `Booking` are declared as attributes.
* **Cascade Rules**: None defined.
* **Default Values**: `created_at` defaults to `datetime.utcnow`.

#### 3. API Layer Support
* **Create**: Supported via `POST /auth/register`.
* **Read / Update / Delete**: Completely missing. There are no endpoints to list users, get user details, update profiles, or delete users.

#### 4. Business Logic
* **Username Uniqueness**: Enforced in `app/routers/auth.py` and via database constraint. However, a duplicate username currently returns `200 OK` (BUG-003) instead of `409 USERNAME_TAKEN`.
* **Role Check**: Enforced via `require_admin` check for administrative tasks.

---

### C. Room

#### 1. Database Schema
* **Table Exists**: Yes, named `rooms` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L36-L43).
* **Required Fields Present**: `id` (Integer, PK), `org_id` (Integer, FK to `organizations.id`), `name` (String), `capacity` (Integer).
* **Missing Required Fields**: **`hourly_rate`** is missing under the specified name (represented as `hourly_rate_cents` instead).
* **Unexpected Fields**: `hourly_rate_cents` (acts as the replacement for the missing `hourly_rate`).
* **Appropriate Types**: Yes.
* **Constraints**: Primary key and foreign key are correct.

#### 2. ORM / Model Layer
* **Model Exists**: Yes, `Room` class in `app/models.py`.
* **Field Names Match**: Mismatch on **`hourly_rate`** (coded as `hourly_rate_cents`).
* **Types Match**: Integer is used for `hourly_rate_cents`, which is appropriate for currency to avoid floating-point errors.
* **Relationships**: No ORM-level relationships to `Organization` or `Booking` are declared as attributes.
* **Cascade Rules**: None defined.

#### 3. API Layer Support
* **Create**: Supported via `POST /rooms` (restricted to admins).
* **Read**: Supported via `GET /rooms` (lists rooms in caller's org) and `/rooms/{id}/availability`.
* **Update / Delete**: Completely missing. No endpoints to update room properties or delete rooms.

#### 4. Business Logic
* **Organization Isolation**: Rooms are correctly filtered by `user.org_id` inside `list_rooms` and `create_room`.

---

### D. Booking

#### 1. Database Schema
* **Table Exists**: Yes, named `bookings` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L46-L57).
* **Required Fields Present**: All required fields (`id`, `room_id`, `user_id`, `start_time`, `end_time`, `status`, `reference_code`, `price_cents`, `created_at`) are present.
* **Missing Required Fields**: None.
* **Unexpected Fields**: None.
* **Appropriate Types**: Yes.
* **Constraints**: Primary key and foreign keys (`room_id`, `user_id`) are correct.

#### 2. ORM / Model Layer
* **Model Exists**: Yes, `Booking` class in `app/models.py`.
* **Field Names Match**: Yes.
* **Types Match**: Yes.
* **Relationships**: Declares `refunds` relationship: `refunds = relationship("RefundLog", backref="booking")`. However, relationships to `User` and `Room` are not declared as attributes.
* **Cascade Rules**: No cascade deletion rules are declared.
* **Default Values**: `status` defaults to `"confirmed"`. `created_at` defaults to `datetime.utcnow`.

#### 3. API Layer Support
* **Create**: Supported via `POST /bookings`.
* **Read**: Supported via `GET /bookings` (list own bookings) and `GET /bookings/{id}` (booking detail).
* **Update**: Partially supported through `POST /bookings/{id}/cancel` (updates status to `"cancelled"`). Other edits are not allowed.
* **Delete**: Hard delete is not supported (only soft cancellation).

#### 4. Business Logic
* **Price Calculation**: Calculates `price_cents = hourly_rate_cents * duration_hours`.
* **Overlap / Quota Validation**: Validates overlap and quota limits.
* **Multi-Tenancy Isolation**: Booking endpoints filter by `Room.org_id == user.org_id` (except the detail endpoint BUG-019 and export BUG-014).

---

### E. RefundLog

#### 1. Database Schema
* **Table Exists**: Yes, named `refund_logs` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L62-L69).
* **Required Fields Present**: `id`, `booking_id`, `amount_cents`, `status`, `processed_at`.
* **Missing Required Fields**: None.
* **Unexpected Fields**: None.
* **Appropriate Types**: Yes.
* **Constraints**: Primary key and foreign key `booking_id` are correct.

#### 2. ORM / Model Layer
* **Model Exists**: Yes, `RefundLog` class in `app/models.py`.
* **Field Names Match**: Yes.
* **Types Match**: Yes.
* **Relationships**: No explicit attributes (configured via `backref="booking"` on `Booking.refunds`).
* **Cascade Rules**: None defined.
* **Default Values**: `processed_at` defaults to `datetime.utcnow`.

#### 3. API Layer Support
* **Create / Read / Update / Delete**: No direct CRUD endpoints exist. Refund logs are created automatically during cancellation and returned nested inside the booking details response `GET /bookings/{id}`.

#### 4. Business Logic
* **Refund Log Creation**: Triggered during booking cancellation in `app/services/refunds.py`.

---

## 2. Relationships Audit

| Source Model | Target Model | Relationship Type | Status in Codebase | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- |
| **Organization** | **User** | One-to-Many | **Missing** | Add `users = relationship("User", backref="organization", cascade="all, delete-orphan")` to `Organization`. |
| **Organization** | **Room** | One-to-Many | **Missing** | Add `rooms = relationship("Room", backref="organization", cascade="all, delete-orphan")` to `Organization`. |
| **Room** | **Booking** | One-to-Many | **Missing** | Add `bookings = relationship("Booking", backref="room", cascade="all, delete-orphan")` to `Room`. |
| **User** | **Booking** | One-to-Many | **Missing** | Add `bookings = relationship("Booking", backref="user", cascade="all, delete-orphan")` to `User`. |
| **Booking** | **RefundLog**| One-to-Many | **Implemented** | Properly mapped via `Booking.refunds = relationship("RefundLog", backref="booking")`. |

---

## 3. Missing Items Audit

1. **Missing Fields**:
   - `created_at` field in the **`organizations`** table.
   - `hourly_rate` field in the **`rooms`** table (implemented as `hourly_rate_cents`).
2. **Missing Mappings**:
   - `Organization` has no ORM relationships to `User` or `Room`.
   - `User` has no ORM relationship to `Booking`.
   - `Room` has no ORM relationship to `Booking`.
3. **Missing API Endpoints**:
   - Complete Organization CRUD endpoints (`GET /organizations`, `GET /organizations/{id}`, `PUT /organizations/{id}`, `DELETE /organizations/{id}`).
   - Complete User CRUD endpoints (`GET /users`, `GET /users/{id}`, `PUT /users/{id}`, `DELETE /users/{id}`).
   - Room detail retrieval, update, and delete endpoints (`GET /rooms/{id}`, `PUT /rooms/{id}`, `DELETE /rooms/{id}`).
   - Booking update and delete endpoints (`PUT /bookings/{id}`, `DELETE /bookings/{id}`).
   - RefundLog listing and detail endpoints.
4. **Missing Database Migrations**:
   - No database migration tool (Alembic) is configured. Table schemas are created dynamically on application startup via `Base.metadata.create_all`.

---

## 4. Extra / Spec Deviant Items

1. **`hourly_rate_cents`** (Room column): This acts as the replacement for the missing `hourly_rate`. It stores monetary rates in cents to avoid floating-point errors. This is **useful** and should be documented but kept to preserve integer arithmetic.
2. **`price_cents`** (Booking column): Not explicitly detailed in the required booking entity but necessary to store historical prices. This is **harmless and useful**.
3. **`amount_cents`** (RefundLog column): Necessary to track the returned refund amount in cents. This is **harmless and useful**.
4. **`reference_code`** (Booking column): Used for client-facing unique references. This is **useful**.

---

## 5. Naming Consistency Audit

* **`hourly_rate`** (Spec) vs **`hourly_rate_cents`** (Codebase): The specification requires `hourly_rate`, but the codebase implements `hourly_rate_cents` in [models.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/models.py#L43) and [schemas.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/schemas.py#L24).
* **`price`** (Conceptual) vs **`price_cents`** (Codebase): The codebase uses `price_cents` throughout to prevent floats.
* **`amount`** (Conceptual) vs **`amount_cents`** (Codebase): Mapped as `amount_cents` in `RefundLog`.

---

## 6. Validation Audit

* **Database Constraints**:
  - `Organization.name`: Unique constraint is correctly set.
  - `User`: Unique constraint on `(org_id, username)` is correctly set.
  - Foreign keys are correctly mapped, but SQLite does not enforce foreign key constraints by default unless `PRAGMA foreign_keys = ON;` is executed on connection.
* **Pydantic Validation**:
  - Exists for requests via `app/schemas.py`, but does not enforce lengths, character sets, or ranges (e.g. `hourly_rate_cents` can accept negative values in `RoomCreateRequest` Pydantic model).

---

## 7. Data Integrity Audit

* **Referential Integrity**: Mapped correctly via SQLAlchemy `ForeignKey`. However, because SQLite requires explicit activation of foreign keys, referential integrity might be bypassed if the connection hook is not configured.
* **Cascade Deletes**: No cascade behavior is defined. Deleting an organization or user will cause SQL Integrity errors or leave orphaned records in SQLite.
* **Unique Constraints**: Unique constraint `uq_user_org_username` is defined in `User`. However, concurrent registrations crash with a `500 Internal Server Error` (IntegrityError) instead of returning a clean error.
* **Transaction Safety**: SQLite transaction locks are not explicitly acquired during read-then-write validations, exposing the application to race conditions (BUG-020, BUG-021, BUG-022).

---

## 8. Line-by-Line Findings

### FIND-001: Missing `created_at` field in `Organization` model
* **File Path**: `app/models.py`
* **File Name**: `models.py`
* **Line Number(s)**: 17–21
* **Model Name**: `Organization`
* **Field Name**: `created_at`
* **Issue Category**: Schema Compliance
* **Severity**: High
* **Description**: The specification requires the `Organization` data model to have a `created_at` timestamp. It is missing from both the ORM model and database schema.
* **Why it is Incorrect**: Violates required data model compliance.
* **Current Implementation**:
```python
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
```
* **Recommended Fix**: Add a `created_at` column to the `Organization` schema.
* **Example Fix**:
```python
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

### FIND-002: Field Naming Mismatch on Room Rate
* **File Path**: `app/models.py`
* **File Name**: `models.py`
* **Line Number(s)**: 43
* **Model Name**: `Room`
* **Field Name**: `hourly_rate`
* **Issue Category**: Naming Consistency
* **Severity**: Medium
* **Description**: The specification requires `hourly_rate`, but the codebase implements `hourly_rate_cents`.
* **Why it is Incorrect**: Mismatch between the required data model specification and the actual codebase attributes.
* **Current Implementation**:
```python
hourly_rate_cents = Column(Integer, nullable=False)
```
* **Recommended Fix**: To keep integer consistency (best practice for currency), document `hourly_rate_cents` as representing `hourly_rate` in cents, or rename the field to `hourly_rate` and adjust computations.

---

### FIND-003: Missing ORM Relationships on entities
* **File Path**: `app/models.py`
* **File Name**: `models.py`
* **Line Number(s)**: 17–70 (Range)
* **Model Name**: All Models
* **Field Name**: Multiple relationship attributes
* **Issue Category**: Architecture / ORM Layer
* **Severity**: Medium
* **Description**: Relationships are missing on the ORM layer, preventing easy traversal of graphs (e.g. `user.organization` or `room.organization`).
* **Why it is Incorrect**: Standard ORM relationships are not declared, requiring manual queries to join tables.
* **Recommended Fix**: Add SQLAlchemy `relationship` mappings to all models.
* **Example Fix**:
```python
# In User class:
organization = relationship("Organization", backref="users")

# In Room class:
organization = relationship("Organization", backref="rooms")
```

---

## 9. Compliance Scores

* **Overall Data Model Compliance Score**: **74%**
* **Organization Model Score**: 60% (Missing `created_at` field and CRUD APIs)
* **User Model Score**: 75% (All fields present, but missing CRUD APIs and relationships)
* **Room Model Score**: 70% (Naming mismatch on `hourly_rate` and missing CRUD APIs)
* **Booking Model Score**: 85% (Contains all fields and most endpoints, missing update endpoints)
* **RefundLog Model Score**: 80% (Contains all fields, missing CRUD endpoints)

---

## 10. Summary Tables

### 1. Missing Fields
* `Organization.created_at`
* `Room.hourly_rate` (named `hourly_rate_cents`)

### 2. Missing Tables
* None (all required core tables are created).

### 3. Missing APIs
* Organization CRUD endpoints.
* User CRUD endpoints.
* Room details, update, and delete endpoints.
* Booking update and hard delete endpoints.

### 4. Missing Relationships (ORM Layer)
* `Organization` &rarr; `User`
* `Organization` &rarr; `Room`
* `User` &rarr; `Booking`
* `Room` &rarr; `Booking`

### 5. Missing Validations
* Pydantic validation on minimum capacity (could be zero/negative).
* Pydantic validation on minimum `hourly_rate_cents` (could be negative).

### 6. Extra Fields (Non-Spec but Present)
* `Booking.price_cents` (Useful)
* `RefundLog.amount_cents` (Useful)
* `Booking.reference_code` (Useful)

### 7. Naming Inconsistencies
* `hourly_rate` (Spec) vs `hourly_rate_cents` (Codebase).

### 8. High-Priority Fixes
1. Add `created_at` column to the `organizations` table.
2. Setup cascade deletes on relationships to prevent database orphan records.
3. Configure `PRAGMA foreign_keys = ON;` in SQLite connections to guarantee referential integrity.
