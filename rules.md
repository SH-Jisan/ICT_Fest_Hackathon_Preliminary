These are the rules the API is expected to follow. Some bugs are deviations from these rules
use them as your source of truth when deciding whether behavior is correct.
1. Datetimes. All API datetimes are ISO 8601. Input datetimes carrying a UTC offset must
be converted to UTC before storage or comparison; naive input is treated as UTC. All
response datetimes are UTC with an explicit UTC designator.
2. Booking price. price
cents = hourly
rate
cents × duration
be a whole number of hours, minimum 1, maximum 8. end
hours. Duration must
time must be strictly after
start
time. start
time must be strictly in the future at request time- no grace window.
3. Nodouble-booking. Twoconfirmedbookingsforthesameroomoverlapiff existing.start
< new.end AND new.start < existing.end. Back-to-back bookings are allowed. Conflict
→409 ROOM
CONFLICT. Must hold under concurrent requests.
4. Booking quota. Amembermayholdatmost3confirmedbookings with start
window (now,now+24h], across all rooms in their org. Violation → 409 QUOTA
Must hold under concurrent requests.
time in the
EXCEEDED.
5. Rate limit. POST /bookings is limited to 20 requests per rolling 60 seconds per user (all
requests count). Excess → 429 RATE
LIMITED. Must hold under concurrent requests.
6. Cancellation refund policy. Only the booking’s owner or an admin of the same org may
cancel. Notice = start
time − cancellation time:
• notice ≥ 48 hours → 100% refund
• 24 hours ≤ notice < 48 hours → 50% refund
• notice < 24 hours → 0% refund
Refund amount rounds to the nearest cent, half-cents rounding up. Cancelling an already
cancelled booking → 409 ALREADY
CANCELLED. A cancelled booking has exactly one Re
fundLog entry, and the amount returned by the cancel response must equal the amount
stored in the RefundLog. Must hold under concurrent cancel requests for the same booking.
7. Reference codes. Every booking’s reference
creation.
code is unique, including under concurrent
8. Auth. Tokens are JWTs (HS256) with claims sub (user id, string), org (org id), role, jti
(unique per token), iat, exp, type (access | refresh). Access tokens expire in exactly
900 seconds. Refresh tokens expire in 7 days. Logout immediately invalidates the presented
access token (subsequent use → 401). Refresh tokens are single-use: refreshing returns a
new access and refresh token and invalidates the presented refresh token (reuse → 401).
9. Multi-tenancy. A user (including admins) may only ever read or act on data belonging to
their own organization, on every code path. Cross-org resource IDs behave as non-existent
(→ 404).
10. Booking visibility. Members may read and cancel only their own bookings (another
member’s booking id → 404 BOOKING
NOT
in their org.
FOUND). Admins may read and cancel any booking
11. Pagination & ordering. GET /bookings takes page (default 1) and limit (default 10,
max 100). Items are the caller’s own bookings sorted ascending by start
time (ties by
ascending id). Sequential pages never skip or repeat items. Response includes total.

12. Usagereport. GET/admin/usage-report?from=...&to=... returns, per roominthe
caller’sorg(includingroomswithzerobookings), thecountandsummedpricecentsof
confirmedbookingsstartingin[from,to](UTC, inclusive).Mustreflectthecurrentstate
immediately.
13. Availability. GET/rooms/{id}/availability?date=... returns the room’sconfirmed
bookings startingon thatUTCdate as busy intervals, sortedascending, reflecting the
currentstateimmediately.
14. Roomstats.GET/rooms/{id}/statsreturnstheroom’scurrentcountofconfirmedbook
ingsandtheirsummedpricecents, alwaysconsistentwiththebookings themselves, in
cludingafterburstsofconcurrentactivity.
15. Registration. POST/auth/registerwithanunknownorgnamecreatestheorgandthe
userasadmin;withaknownorgnameitjoinsthecallerasmember.Aduplicateusername
withintheorg→409USERNAMETAKEN.
16. Liveness. Theservicemustrespondtoall endpointsatall times;nocombinationofcon
currentvalidrequestsmayhangtheservice