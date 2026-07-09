"""Live per-room booking statistics.

Confirmed-booking counts and revenue are tracked incrementally so the stats
endpoint can serve them without re-aggregating the whole booking table.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Booking


def record_create(room_id: int, price_cents: int) -> None:
    # Retained for backward compatibility / caller routes but no longer used for reads
    pass


def record_cancel(room_id: int, price_cents: int) -> None:
    # Retained for backward compatibility / caller routes but no longer used for reads
    pass


def get(db: Session, room_id: int) -> dict:
    row = (
        db.query(
            func.count(Booking.id).label("count"),
            func.coalesce(func.sum(Booking.price_cents), 0).label("revenue"),
        )
        .filter(Booking.room_id == room_id, Booking.status == "confirmed")
        .first()
    )
    return {"count": row.count or 0, "revenue": row.revenue or 0}
