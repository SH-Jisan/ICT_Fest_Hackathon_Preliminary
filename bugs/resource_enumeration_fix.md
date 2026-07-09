# Bug: Resource Enumeration on Room CSV Export

## Summary
The export endpoint accepted a `room_id` query parameter and generated a CSV report without verifying that the room belonged to the administrator's organization, returning a `200 OK` (with either competitor details or an empty CSV) instead of an `HTTP 404 Not Found`.

## Rule Violated
> **Whenever a user attempts to access a resource belonging to another organization, the application must behave exactly as if the resource does not exist and return HTTP 404 Not Found.**

## Severity
High

## Affected Files
* [app/routers/admin.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/admin.py)

## Modified Line Numbers
* `admin.py` : Lines 69–74

## Original Code
```python
@router.get("/export")
def export(
    room_id: int | None = Query(None),
    include_all: bool = Query(False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    csv_body = generate_export(db, admin.org_id, admin.id, room_id, include_all)
    return Response(content=csv_body, media_type="text/csv")
```

## Fixed Code
```python
@router.get("/export")
def export(
    room_id: int | None = Query(None),
    include_all: bool = Query(False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if room_id is not None:
        room = db.query(Room).filter(Room.id == room_id, Room.org_id == admin.org_id).first()
        if room is None:
            raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
            
    csv_body = generate_export(db, admin.org_id, admin.id, room_id, include_all)
    return Response(content=csv_body, media_type="text/csv")
```

## Root Cause
No route-level validation of room organization ownership.

## Fix Applied
Added a check to query the room by ID and organization ID, raising a `404 ROOM_NOT_FOUND` if the room does not exist in the admin's organization scope.

## Why the Fix Works
Prevents resource enumeration by returning 404 if a room belonging to another organization is queried.

## Concurrency Notes
N/A

## Tests Updated
Added tests in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L539-L592).
