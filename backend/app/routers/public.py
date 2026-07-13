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
    PublicReservedTicketItem,
    PublicTicketReserveCreate,
    PublicTicketReserveResponse,
    PublicTicketResponse,
)
from app.services.ticket_generator import (
    get_effective_max_tickets,
    normalize_ticket_number,
)
from app.services.ticket_image_service import generate_ticket_image
from app.utils.short_code import generate_unique_short_code

router = APIRouter(prefix="/api/public", tags=["public"])

PAYMENT_PROOFS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "payment-proofs"
ALLOWED_PROOF_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}
MAX_PROOF_BYTES = 5 * 1024 * 1024
MAX_TICKETS_PER_RESERVATION = 20


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


def _get_reservation_group(ticket: Ticket, db: Session) -> list[Ticket]:
    if not ticket.reservation_group_id:
        return [ticket]
    return (
        db.query(Ticket)
        .filter(Ticket.reservation_group_id == ticket.reservation_group_id)
        .order_by(Ticket.ticket_number)
        .all()
    )


def _build_payment_status(ticket: Ticket, db: Session) -> PublicPaymentStatusResponse:
    group = _get_reservation_group(ticket, db)
    raffle = ticket.raffle
    unit_price = Decimal(str(raffle.ticket_price))
    ticket_numbers = [t.ticket_number for t in group]
    proof_ticket = next((t for t in group if t.payment_proof_filename), ticket)
    all_paid = all(t.is_paid for t in group)
    has_proof = any(t.payment_proof_filename for t in group)
    proof_uploaded_at = proof_ticket.payment_proof_uploaded_at if has_proof else None

    return PublicPaymentStatusResponse(
        public_id=ticket.public_id,
        ticket_number=ticket.ticket_number,
        ticket_numbers=ticket_numbers,
        raffle_name=raffle.name,
        buyer_name=ticket.buyer_name,
        ticket_price=unit_price,
        total_price=unit_price * len(group),
        is_paid=all_paid,
        has_payment_proof=has_proof,
        payment_proof_uploaded_at=proof_uploaded_at,
        payment_proof_url=_payment_proof_url(proof_ticket) if has_proof else None,
        reservation_group_id=ticket.reservation_group_id,
    )


def _apply_payment_proof_to_group(group: list[Ticket], filename: str, uploaded_at: datetime) -> None:
    for member in group:
        if member.is_paid:
            continue
        member.payment_proof_filename = filename
        member.payment_proof_uploaded_at = uploaded_at


def _delete_group_payment_proofs(group: list[Ticket]) -> None:
    seen: set[str] = set()
    for member in group:
        if member.payment_proof_filename and member.payment_proof_filename not in seen:
            seen.add(member.payment_proof_filename)
            _delete_payment_proof_file(member)


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

    if len(data.ticket_numbers) > MAX_TICKETS_PER_RESERVATION:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo {MAX_TICKETS_PER_RESERVATION} tickets por reserva",
        )

    taken = _taken_numbers(raffle.id, db)
    max_t = get_effective_max_tickets(raffle, taken)
    normalized: list[str] = []

    for raw_number in data.ticket_numbers:
        try:
            ticket_number = normalize_ticket_number(raw_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if int(ticket_number) > max_t:
            raise HTTPException(
                status_code=400,
                detail=f"El número {ticket_number} supera el máximo disponible ({max_t:04d})",
            )
        if ticket_number in taken:
            raise HTTPException(status_code=409, detail=f"El número {ticket_number} ya no está disponible")
        if ticket_number in normalized:
            raise HTTPException(status_code=400, detail=f"El número {ticket_number} está repetido en tu selección")

        normalized.append(ticket_number)

    group_id = str(uuid.uuid4()) if len(normalized) > 1 else None
    created: list[Ticket] = []

    for ticket_number in normalized:
        ticket = Ticket(
            raffle_id=raffle.id,
            ticket_number=ticket_number,
            short_code=generate_unique_short_code(db),
            buyer_name=data.buyer_name,
            buyer_phone=data.buyer_phone,
            buyer_email=str(data.buyer_email) if data.buyer_email else None,
            is_paid=False,
            reservation_group_id=group_id,
        )
        db.add(ticket)
        created.append(ticket)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Uno o más números ya no están disponibles")

    for ticket in created:
        db.refresh(ticket)

    unit_price = Decimal(str(raffle.ticket_price))
    count = len(created)
    message = (
        "Tus números fueron reservados. Completá el pago y enviá tu comprobante."
        if count > 1
        else "Tu número fue reservado. Completá el pago y enviá tu comprobante."
    )

    return PublicTicketReserveResponse(
        reservation_group_id=group_id,
        tickets=[
            PublicReservedTicketItem(public_id=t.public_id, ticket_number=t.ticket_number)
            for t in created
        ],
        raffle_name=raffle.name,
        buyer_name=data.buyer_name,
        ticket_price=unit_price,
        total_price=unit_price * count,
        message=message,
    )


@router.get("/tickets/{public_id}/payment", response_model=PublicPaymentStatusResponse)
def get_payment_status(public_id: str, db: Session = Depends(get_db)):
    ticket = _get_ticket_by_public_id(public_id, db)
    return _build_payment_status(ticket, db)


@router.post("/tickets/{public_id}/payment-proof", response_model=PublicPaymentStatusResponse)
async def upload_payment_proof(
    public_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ticket = _get_ticket_by_public_id(public_id, db)
    group = _get_reservation_group(ticket, db)

    if all(t.is_paid for t in group):
        raise HTTPException(status_code=400, detail="Estos tickets ya están confirmados como pagados")

    if file.content_type not in ALLOWED_PROOF_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Usá JPG, PNG, WEBP, GIF o PDF.",
        )

    content = await file.read()
    if len(content) > MAX_PROOF_BYTES:
        raise HTTPException(status_code=400, detail="El archivo no puede superar 5 MB.")

    PAYMENT_PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    _delete_group_payment_proofs(group)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    if file.content_type == "application/pdf":
        ext = "pdf"
    filename = f"{uuid.uuid4()}.{ext}"
    (PAYMENT_PROOFS_DIR / filename).write_bytes(content)

    uploaded_at = datetime.utcnow()
    _apply_payment_proof_to_group(group, filename, uploaded_at)
    db.commit()
    db.refresh(ticket)

    return _build_payment_status(ticket, db)


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
