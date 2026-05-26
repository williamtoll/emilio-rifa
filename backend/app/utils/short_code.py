import secrets
import string

from sqlalchemy.orm import Session

from app.models import Ticket

_ALPHABET = string.ascii_letters + string.digits
_LENGTH = 8


def generate_unique_short_code(db: Session) -> str:
    for _ in range(30):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))
        exists = db.query(Ticket.id).filter(Ticket.short_code == code).first()
        if not exists:
            return code
    raise RuntimeError("No se pudo generar un enlace corto único")
