# Bug: Timezone Offset Dropped Without Normalization

## Summary
The datetime parsing utility dropped timezone offset metadata from incoming ISO 8601 string datetimes directly without converting the datetime to the UTC timezone first.

## Rule Violated
> **Input datetimes carrying a UTC offset must be converted to UTC before storage or comparison; naive input is treated as UTC.**

## Affected Files
* [app/timeutils.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/timeutils.py)

## Line Numbers
* `timeutils.py` : Lines 11–14

## Root Cause
The `parse_input_datetime` function invoked `dt.replace(tzinfo=None)` directly on the parsed datetime object. In Python, `.replace(tzinfo=None)` strips the timezone metadata but does not shift the hour or minute values to reflect the timezone conversion, leaving local time hours as if they were UTC hours.

## Previous Behavior
If a client sent a datetime string with an offset (e.g. `2026-07-09T18:00:00+06:00`), `parse_input_datetime` stripped the offset directly, returning a naive datetime representing `18:00:00` UTC instead of `12:00:00` UTC.

## New Behavior
When a datetime with an offset is received, it is converted to the UTC timezone first using `.astimezone(timezone.utc)` and then stripped of its timezone metadata. For example, `2026-07-09T18:00:00+06:00` is now correctly parsed as `12:00:00` UTC.

## Fix Applied
Changed `.replace(tzinfo=None)` to `.astimezone(timezone.utc).replace(tzinfo=None)` when a timezone offset is present.

## Why This Fix Works
Applying `.astimezone(timezone.utc)` shifts the datetime values (hours and minutes) to reflect their correct value in the UTC timezone before we strip the metadata for SQLite naive datetime storage, achieving full compliance.

## Files Modified
* [app/timeutils.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/timeutils.py)

## Related Issue
* `DT-001` (from `datetime_compliance_audit.md`)

## Notes
None.
