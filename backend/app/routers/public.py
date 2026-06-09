from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Raffle, Ticket
from app.schemas import PrizeResponse, PublicTicketResponse
from app.services.ticket_image_service import generate_ticket_image

router = APIRouter(prefix="/api/public", tags=["public"])


def _prize_image_url(prize) -> str | None:
    if not prize.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/prizes/{prize.image_filename}"


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
