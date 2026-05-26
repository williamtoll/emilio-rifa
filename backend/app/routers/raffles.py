from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Raffle, Ticket
from app.schemas import RaffleCreate, RaffleResponse, RaffleUpdate

router = APIRouter(
    prefix="/api/raffles",
    tags=["raffles"],
    dependencies=[Depends(get_current_user)],
)


def _raffle_to_response(raffle: Raffle, db: Session) -> RaffleResponse:
    tickets = db.query(Ticket).filter(Ticket.raffle_id == raffle.id).all()
    return RaffleResponse(
        id=raffle.id,
        name=raffle.name,
        description=raffle.description,
        ticket_price=raffle.ticket_price,
        is_active=raffle.is_active,
        created_at=raffle.created_at,
        ticket_count=len(tickets),
        paid_count=sum(1 for t in tickets if t.is_paid),
    )


@router.get("", response_model=list[RaffleResponse])
def list_raffles(db: Session = Depends(get_db)):
    raffles = db.query(Raffle).order_by(Raffle.created_at.desc()).all()
    return [_raffle_to_response(r, db) for r in raffles]


@router.post("", response_model=RaffleResponse, status_code=201)
def create_raffle(data: RaffleCreate, db: Session = Depends(get_db)):
    raffle = Raffle(**data.model_dump())
    db.add(raffle)
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.get("/{raffle_id}", response_model=RaffleResponse)
def get_raffle(raffle_id: int, db: Session = Depends(get_db)):
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return _raffle_to_response(raffle, db)


@router.patch("/{raffle_id}", response_model=RaffleResponse)
def update_raffle(raffle_id: int, data: RaffleUpdate, db: Session = Depends(get_db)):
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(raffle, key, value)
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.delete("/{raffle_id}", status_code=204)
def delete_raffle(raffle_id: int, db: Session = Depends(get_db)):
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    db.delete(raffle)
    db.commit()
