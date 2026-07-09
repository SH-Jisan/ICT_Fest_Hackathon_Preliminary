# Bug: Unhandled ValueError on Malformed ISO 8601 Datetime String

## Summary
The booking creation endpoint crashed with a `500 Internal Server Error` instead of returning a proper validation error when given a malformed or invalid ISO 8601 datetime string.

## Rule Violated
> **All API datetimes are ISO 8601.** (Implicitly: Invalid datetime formats must be rejected with proper validation errors).

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Line Numbers
* `bookings.py` : Lines 81–84

## Root Cause
The `create_booking` endpoint called `parse_input_datetime` without catching `ValueError`. If a client supplied a malformed datetime string, `datetime.fromisoformat` threw a `ValueError` which bubbled up and crashed the request handler.

## Previous Behavior
Sending a malformed start/end time string (e.g. `"invalid-date"`) to `POST /bookings` caused an unhandled python exception, yielding a `500 Internal Server Error` response.

## New Behavior
Invalid ISO 8601 strings are caught, and the endpoint throws a clean `400 Bad Request` AppError with the code `INVALID_BOOKING_WINDOW`.

## Fix Applied
Wrapped the `parse_input_datetime` calls inside a `try-except ValueError` block and raised `AppError(400, "INVALID_BOOKING_WINDOW", "Invalid datetime format")` when exceptions are caught.

## Why This Fix Works
It intercepts the parsing exception, prevents request handler crashes, and formats the validation failure into a standard JSON error response that conforms to the API's contract.

## Files Modified
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Related Issue
* `DT-002` (from `datetime_compliance_audit.md`)

## Notes
None.
