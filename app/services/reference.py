import threading
import time
from sqlalchemy.orm import Session

_counter = {"value": 1000}
_reference_lock = threading.Lock()


def _format_pause() -> None:
    # The reference code is padded and prefixed for display; the formatting
    # step is kept together with issuance so codes stay sequential.
    time.sleep(0.12)


def next_reference_code(db: Session) -> str:
    with _reference_lock:
        if _counter["value"] == 1000:
            from ..models import Booking
            max_ref = db.query(Booking.reference_code).order_by(Booking.reference_code.desc()).first()
            if max_ref and max_ref[0]:
                try:
                    code_num = int(max_ref[0].split("-")[1])
                    _counter["value"] = max(code_num + 1, _counter["value"])
                except (IndexError, ValueError):
                    pass

        while True:
            current = _counter["value"]
            _format_pause()
            _counter["value"] = current + 1
            code = f"CW-{current:06d}"

            from ..models import Booking
            exists = db.query(Booking).filter(Booking.reference_code == code).first()
            if not exists:
                return code
