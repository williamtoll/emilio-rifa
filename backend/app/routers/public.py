from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Ticket
from app.schemas import PublicTicketResponse
from app.services.ticket_image_service import generate_ticket_image

router = APIRouter(prefix="/api/public", tags=["public"])


def _get_paid_ticket(public_id: str, db: Session) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.raffle))
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
    return PublicTicketResponse(
        public_id=ticket.public_id,
        ticket_number=ticket.ticket_number,
        buyer_name=ticket.buyer_name,
        raffle_name=raffle.name,
        ticket_price=raffle.ticket_price,
        is_paid=ticket.is_paid,
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
