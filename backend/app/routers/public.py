from datetime import datetime
from decimal import Decimal
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Prize, Raffle, Ticket
from app.schemas import (
    PrizeResponse,
    PublicAvailabilityResponse,
    PublicPaymentStatusResponse,
    PublicRaffleDetail,
    PublicRaffleSummary,
    PublicTicketReserveCreate,
    PublicTicketReserveResponse,
    PublicTicketResponse,
)
from app.services.ticket_generator import (
    get_effective_max_tickets,
    is_ticket_number_available,
    normalize_ticket_number,
)
from app.services.ticket_image_service import generate_ticket_image
from app.utils.short_code import generate_unique_short_code

router = APIRouter(prefix="/api/public", tags=["public"])

PAYMENT_PROOFS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "payment-proofs"
ALLOWED_PROOF_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}
MAX_PROOF_BYTES = 5 * 1024 * 1024


def _prize_image_url(prize: Prize) -> str | None:
    if not prize.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/prizes/{prize.image_filename}"


def _raffle_image_url(raffle: Raffle) -> str | None:
    if not raffle.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/raffles/{raffle.image_filename}"


def _payment_proof_url(ticket: Ticket) -> str | None:
    if not ticket.payment_proof_filename:
        return None
    return f"{settings.app_base_url}/uploads/payment-proofs/{ticket.payment_proof_filename}"


def _get_ticket_by_public_id(public_id: str, db: Session) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.raffle))
        .filter(Ticket.public_id == public_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


def _delete_payment_proof_file(ticket: Ticket) -> None:
    if not ticket.payment_proof_filename:
        return
    path = PAYMENT_PROOFS_DIR / ticket.payment_proof_filename
    if path.exists():
        path.unlink()


def _is_raffle_open(raffle: Raffle) -> bool:
    return raffle.is_active and raffle.draw_closed_at is None


def _get_open_raffle(raffle_id: int, db: Session) -> Raffle:
    raffle = (
        db.query(Raffle)
        .options(joinedload(Raffle.prizes))
        .filter(Raffle.id == raffle_id)
        .first()
    )
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    if not _is_raffle_open(raffle):
        raise HTTPException(status_code=404, detail="Sorteo no disponible")
    return raffle


def _taken_numbers(raffle_id: int, db: Session) -> list[str]:
    rows = db.query(Ticket.ticket_number).filter(Ticket.raffle_id == raffle_id).all()
    return sorted({r[0] for r in rows}, key=lambda n: int(n) if n.isdigit() else n)


def _raffle_summary(raffle: Raffle, db: Session) -> PublicRaffleSummary:
    taken = _taken_numbers(raffle.id, db)
    max_t = get_effective_max_tickets(raffle, taken)
    sold = len(taken)
    return PublicRaffleSummary(
        id=raffle.id,
        name=raffle.name,
        description=raffle.description,
        ticket_price=raffle.ticket_price,
        image_url=_raffle_image_url(raffle),
        max_tickets=raffle.max_tickets or max_t,
        tickets_sold=sold,
        tickets_available=max(0, max_t - sold),
    )


def _get_paid_ticket(public_id: str, db: Session) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.raffle).joinedload(Raffle.prizes))
        .filter(Ticket.public_id == public_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if not ticket.is_paid:
        raise HTTPException(status_code=404, detail="Ticket no disponible")
    return ticket


@router.get("/raffles", response_model=list[PublicRaffleSummary])
def list_public_raffles(db: Session = Depends(get_db)):
    raffles = (
        db.query(Raffle)
        .filter(Raffle.is_active.is_(True), Raffle.draw_closed_at.is_(None))
        .order_by(Raffle.created_at.desc())
        .all()
    )
    return [_raffle_summary(r, db) for r in raffles]


@router.get("/raffles/{raffle_id}", response_model=PublicRaffleDetail)
def get_public_raffle(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_open_raffle(raffle_id, db)
    taken = _taken_numbers(raffle.id, db)
    max_t = get_effective_max_tickets(raffle, taken)
    sold = len(taken)
    prizes = sorted(raffle.prizes, key=lambda p: p.order) if raffle.prizes else []
    return PublicRaffleDetail(
        id=raffle.id,
        name=raffle.name,
        description=raffle.description,
        ticket_price=raffle.ticket_price,
        image_url=_raffle_image_url(raffle),
        max_tickets=raffle.max_tickets or max_t,
        tickets_sold=sold,
        tickets_available=max(0, max_t - sold),
        prizes=[
            PrizeResponse(
                id=p.id,
                raffle_id=p.raffle_id,
                name=p.name,
                description=p.description,
                order=p.order,
                image_filename=p.image_filename,
                image_url=_prize_image_url(p),
            )
            for p in prizes
        ],
    )


@router.get("/raffles/{raffle_id}/availability", response_model=PublicAvailabilityResponse)
def get_raffle_availability(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_open_raffle(raffle_id, db)
    taken = _taken_numbers(raffle.id, db)
    max_t = get_effective_max_tickets(raffle, taken)
    return PublicAvailabilityResponse(raffle_id=raffle.id, max_tickets=max_t, taken=taken)


@router.post("/raffles/{raffle_id}/tickets", response_model=PublicTicketReserveResponse, status_code=201)
def reserve_public_ticket(
    raffle_id: int,
    data: PublicTicketReserveCreate,
    db: Session = Depends(get_db),
):
    raffle = _get_open_raffle(raffle_id, db)

    try:
        ticket_number = normalize_ticket_number(data.ticket_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    taken = _taken_numbers(raffle.id, db)
    max_t = get_effective_max_tickets(raffle, taken)
    if int(ticket_number) > max_t:
        raise HTTPException(status_code=400, detail=f"El número máximo disponible es {max_t:04d}")

    if not is_ticket_number_available(db, raffle.id, ticket_number):
        raise HTTPException(status_code=409, detail="Ese número ya no está disponible")

    ticket = Ticket(
        raffle_id=raffle.id,
        ticket_number=ticket_number,
        short_code=generate_unique_short_code(db),
        buyer_name=data.buyer_name,
        buyer_phone=data.buyer_phone,
        buyer_email=str(data.buyer_email) if data.buyer_email else None,
        is_paid=False,
    )
    db.add(ticket)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ese número ya no está disponible")

    db.refresh(ticket)

    return PublicTicketReserveResponse(
        public_id=ticket.public_id,
        ticket_number=ticket_number,
        raffle_name=raffle.name,
        buyer_name=data.buyer_name,
        ticket_price=Decimal(str(raffle.ticket_price)),
    )


@router.get("/tickets/{public_id}/payment", response_model=PublicPaymentStatusResponse)
def get_payment_status(public_id: str, db: Session = Depends(get_db)):
    ticket = _get_ticket_by_public_id(public_id, db)
    raffle = ticket.raffle
    return PublicPaymentStatusResponse(
        public_id=ticket.public_id,
        ticket_number=ticket.ticket_number,
        raffle_name=raffle.name,
        buyer_name=ticket.buyer_name,
        ticket_price=Decimal(str(raffle.ticket_price)),
        is_paid=ticket.is_paid,
        has_payment_proof=bool(ticket.payment_proof_filename),
        payment_proof_uploaded_at=ticket.payment_proof_uploaded_at,
        payment_proof_url=_payment_proof_url(ticket),
    )


@router.post("/tickets/{public_id}/payment-proof", response_model=PublicPaymentStatusResponse)
async def upload_payment_proof(
    public_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ticket = _get_ticket_by_public_id(public_id, db)

    if ticket.is_paid:
        raise HTTPException(status_code=400, detail="Este ticket ya está confirmado como pagado")

    if file.content_type not in ALLOWED_PROOF_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Usá JPG, PNG, WEBP, GIF o PDF.",
        )

    content = await file.read()
    if len(content) > MAX_PROOF_BYTES:
        raise HTTPException(status_code=400, detail="El archivo no puede superar 5 MB.")

    PAYMENT_PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    _delete_payment_proof_file(ticket)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    if file.content_type == "application/pdf":
        ext = "pdf"
    filename = f"{uuid.uuid4()}.{ext}"
    (PAYMENT_PROOFS_DIR / filename).write_bytes(content)

    ticket.payment_proof_filename = filename
    ticket.payment_proof_uploaded_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)

    raffle = ticket.raffle
    return PublicPaymentStatusResponse(
        public_id=ticket.public_id,
        ticket_number=ticket.ticket_number,
        raffle_name=raffle.name,
        buyer_name=ticket.buyer_name,
        ticket_price=Decimal(str(raffle.ticket_price)),
        is_paid=ticket.is_paid,
        has_payment_proof=True,
        payment_proof_uploaded_at=ticket.payment_proof_uploaded_at,
        payment_proof_url=_payment_proof_url(ticket),
    )


@router.get("/tickets/{public_id}", response_model=PublicTicketResponse)
def get_public_ticket(public_id: str, db: Session = Depends(get_db)):
    ticket = _get_paid_ticket(public_id, db)
    raffle = ticket.raffle
    prizes = sorted(raffle.prizes, key=lambda p: p.order) if raffle.prizes else []
    return PublicTicketResponse(
        public_id=ticket.public_id,
        ticket_number=ticket.ticket_number,
        buyer_name=ticket.buyer_name,
        raffle_name=raffle.name,
        ticket_price=raffle.ticket_price,
        is_paid=ticket.is_paid,
        prizes=[
            PrizeResponse(
                id=p.id,
                raffle_id=p.raffle_id,
                name=p.name,
                description=p.description,
                order=p.order,
                image_filename=p.image_filename,
                image_url=_prize_image_url(p),
            )
            for p in prizes
        ],
    )


@router.get("/tickets/{public_id}/image")
def get_public_ticket_image(public_id: str, db: Session = Depends(get_db)):
    ticket = _get_paid_ticket(public_id, db)
    image_bytes = generate_ticket_image(ticket)
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="ticket-{ticket.ticket_number}.png"'},
    )
