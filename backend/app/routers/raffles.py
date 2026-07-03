import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Prize, Raffle, Ticket
from app.schemas import PrizeResponse, RaffleCreate, RaffleResponse, RaffleUpdate

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "raffles"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(
    prefix="/api/raffles",
    tags=["raffles"],
    dependencies=[Depends(get_current_user)],
)


def _prize_image_url(prize: Prize) -> str | None:
    if not prize.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/prizes/{prize.image_filename}"


def _raffle_image_url(raffle: Raffle) -> str | None:
    if not raffle.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/raffles/{raffle.image_filename}"


def _raffle_to_response(raffle: Raffle, db: Session) -> RaffleResponse:
    tickets = db.query(Ticket).filter(Ticket.raffle_id == raffle.id).all()
    prizes = db.query(Prize).filter(Prize.raffle_id == raffle.id).order_by(Prize.order).all()
    return RaffleResponse(
        id=raffle.id,
        name=raffle.name,
        description=raffle.description,
        ticket_price=raffle.ticket_price,
        is_active=raffle.is_active,
        draw_closed_at=raffle.draw_closed_at,
        image_filename=raffle.image_filename,
        image_url=_raffle_image_url(raffle),
        max_tickets=raffle.max_tickets,
        created_at=raffle.created_at,
        ticket_count=len(tickets),
        paid_count=sum(1 for t in tickets if t.is_paid),
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


def _get_raffle_or_404(raffle_id: int, db: Session) -> Raffle:
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return raffle


def _delete_raffle_image_file(raffle: Raffle) -> None:
    if not raffle.image_filename:
        return
    path = UPLOADS_DIR / raffle.image_filename
    if path.exists():
        path.unlink()


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
    raffle = _get_raffle_or_404(raffle_id, db)
    return _raffle_to_response(raffle, db)


@router.patch("/{raffle_id}", response_model=RaffleResponse)
def update_raffle(raffle_id: int, data: RaffleUpdate, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(raffle, key, value)
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.post("/{raffle_id}/image", response_model=RaffleResponse)
async def upload_raffle_image(
    raffle_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raffle = _get_raffle_or_404(raffle_id, db)

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Usá JPG, PNG, WEBP o GIF.")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    _delete_raffle_image_file(raffle)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    (UPLOADS_DIR / filename).write_bytes(content)

    raffle.image_filename = filename
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.delete("/{raffle_id}/image", response_model=RaffleResponse)
def delete_raffle_image(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    _delete_raffle_image_file(raffle)
    raffle.image_filename = None
    db.commit()
    db.refresh(raffle)
    return _raffle_to_response(raffle, db)


@router.delete("/{raffle_id}", status_code=204)
def delete_raffle(raffle_id: int, db: Session = Depends(get_db)):
    raffle = _get_raffle_or_404(raffle_id, db)
    _delete_raffle_image_file(raffle)
    db.delete(raffle)
    db.commit()
