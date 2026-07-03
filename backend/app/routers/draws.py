import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import DrawResult, Prize, Raffle, Ticket
from app.schemas import DrawResultResponse, RaffleResponse
from app.routers.raffles import _raffle_to_response

router = APIRouter(
    prefix="/api/raffles/{raffle_id}/draw-results",
    tags=["draws"],
    dependencies=[Depends(get_current_user)],
)


def _result_to_response(r: DrawResult) -> DrawResultResponse:
    return DrawResultResponse(
        id=r.id,
        raffle_id=r.raffle_id,
        prize_id=r.prize_id,
        prize_name=r.prize.name,
        prize_order=r.prize.order,
        ticket_id=r.ticket_id,
        ticket_number=r.ticket.ticket_number,
        buyer_name=r.ticket.buyer_name,
        buyer_phone=r.ticket.buyer_phone,
        drawn_at=r.drawn_at,
    )


def _get_raffle_or_404(raffle_id: int, db: Session) -> Raffle:
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return raffle


def _ensure_draw_open(raffle: Raffle) -> None:
    if raffle.draw_closed_at is not None:
        raise HTTPException(status_code=403, detail="El sorteo está cerrado y no se puede modificar")


@router.get("", response_model=list[DrawResultResponse])
def list_draw_results(raffle_id: int, db: Session = Depends(get_db)):
    _get_raffle_or_404(raffle_id, db)
    results = (
        db.query(DrawResult)
        .options(joinedload(DrawResult.prize), joinedload(DrawResult.ticket))
        .filter(DrawResult.raffle_id == raffle_id)
        .order_by(DrawResult.drawn_at.asc())
        .all()
    )
    return [_result_to_response(r) for r in results]


@router.post("/close", response_model=RaffleResponse)
def close_draw(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)

    if raffle.draw_closed_at is not None:
        raise HTTPException(status_code=409, detail="El sorteo ya está cerrado")

    prizes = db.query(Prize).filter(Prize.raffle_id == raffle_id).all()
    if not prizes:
        raise HTTPException(status_code=422, detail="El sorteo no tiene premios definidos")

    drawn_prize_ids = {
        r.prize_id
        for r in db.query(DrawResult.prize_id).filter(DrawResult.raffle_id == raffle_id).all()
    }
    missing = [p for p in prizes if p.id not in drawn_prize_ids]
    if missing:
        raise HTTPException(
            status_code=422,
            detail="Todos los premios deben estar sorteados antes de cerrar el sorteo",
        )

    raffle.draw_closed_at = datetime.utcnow()
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.post("/{prize_id}", response_model=DrawResultResponse, status_code=201)
def draw_winner(raffle_id: int, prize_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    _ensure_draw_open(raffle)

    prize = db.query(Prize).filter(Prize.id == prize_id, Prize.raffle_id == raffle_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="Premio no encontrado")

    existing = db.query(DrawResult).filter(
        DrawResult.raffle_id == raffle_id,
        DrawResult.prize_id == prize_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Este premio ya tiene un ganador sorteado")

    already_won_ids = {
        r.ticket_id
        for r in db.query(DrawResult.ticket_id).filter(DrawResult.raffle_id == raffle_id).all()
    }

    eligible = (
        db.query(Ticket)
        .filter(
            Ticket.raffle_id == raffle_id,
            Ticket.is_paid.is_(True),
            Ticket.id.notin_(already_won_ids) if already_won_ids else True,
        )
        .all()
    )

    if not eligible:
        raise HTTPException(
            status_code=422,
            detail="No hay tickets pagados disponibles para sortear (todos ya fueron premiados o no hay tickets pagados)",
        )

    winner = random.choice(eligible)

    result = DrawResult(raffle_id=raffle_id, prize_id=prize_id, ticket_id=winner.id)
    db.add(result)
    db.commit()
    db.refresh(result)

    result = (
        db.query(DrawResult)
        .options(joinedload(DrawResult.prize), joinedload(DrawResult.ticket))
        .filter(DrawResult.id == result.id)
        .first()
    )
    return _result_to_response(result)


@router.delete("/{prize_id}", status_code=204)
def undo_prize_draw(raffle_id: int, prize_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    _ensure_draw_open(raffle)

    result = db.query(DrawResult).filter(
        DrawResult.raffle_id == raffle_id,
        DrawResult.prize_id == prize_id,
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="No hay resultado para este premio")
    db.delete(result)
    db.commit()


@router.delete("", status_code=204)
def reset_all_draws(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    _ensure_draw_open(raffle)
    db.query(DrawResult).filter(DrawResult.raffle_id == raffle_id).delete()
    db.commit()
