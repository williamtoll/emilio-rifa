from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Raffle, Ticket
from app.schemas import (
    SendTicketRequest,
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    WhatsAppLinkResponse,
)
from app.services.email_service import send_ticket_email
from app.services.ticket_generator import generate_ticket_number
from app.services.ticket_image_service import generate_ticket_image
from app.services.whatsapp_service import build_whatsapp_url

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _ticket_to_response(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        raffle_id=ticket.raffle_id,
        ticket_number=ticket.ticket_number,
        buyer_name=ticket.buyer_name,
        buyer_phone=ticket.buyer_phone,
        buyer_email=ticket.buyer_email,
        is_paid=ticket.is_paid,
        created_at=ticket.created_at,
        raffle_name=ticket.raffle.name if ticket.raffle else None,
    )


@router.get("", response_model=list[TicketResponse])
def list_tickets(raffle_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Ticket).options(joinedload(Ticket.raffle))
    if raffle_id is not None:
        query = query.filter(Ticket.raffle_id == raffle_id)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return [_ticket_to_response(t) for t in tickets]


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    raffle = db.query(Raffle).filter(Raffle.id == data.raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    ticket_number = generate_ticket_number(db, data.raffle_id)
    ticket = Ticket(
        raffle_id=data.raffle_id,
        ticket_number=ticket_number,
        buyer_name=data.buyer_name,
        buyer_phone=data.buyer_phone,
        buyer_email=str(data.buyer_email) if data.buyer_email else None,
        is_paid=False,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket.id).first()
    return _ticket_to_response(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return _ticket_to_response(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    if "buyer_email" in update_data and update_data["buyer_email"] is not None:
        update_data["buyer_email"] = str(update_data["buyer_email"])

    for key, value in update_data.items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(ticket)


@router.post("/{ticket_id}/mark-paid", response_model=TicketResponse)
def mark_ticket_paid(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket.is_paid = True
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(ticket)


@router.post("/{ticket_id}/mark-unpaid", response_model=TicketResponse)
def mark_ticket_unpaid(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket.is_paid = False
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(ticket)


@router.post("/{ticket_id}/send-email")
async def send_email(ticket_id: int, body: SendTicketRequest = SendTicketRequest(), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    try:
        await send_ticket_email(ticket, body.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Correo enviado correctamente"}


@router.get("/{ticket_id}/image")
def get_ticket_image(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    image_bytes = generate_ticket_image(ticket)
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="ticket-{ticket.ticket_number}.png"'},
    )


@router.get("/{ticket_id}/whatsapp-link", response_model=WhatsAppLinkResponse)
def whatsapp_link(ticket_id: int, message: str | None = None, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).options(joinedload(Ticket.raffle)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    try:
        url, text = build_whatsapp_url(ticket, message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return WhatsAppLinkResponse(url=url, message=text)
