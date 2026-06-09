import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Prize, Raffle
from app.schemas import PrizeCreate, PrizeResponse, PrizeUpdate

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "prizes"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(
    prefix="/api/raffles/{raffle_id}/prizes",
    tags=["prizes"],
    dependencies=[Depends(get_current_user)],
)


def _prize_image_url(prize: Prize) -> str | None:
    if not prize.image_filename:
        return None
    return f"{settings.app_base_url}/uploads/prizes/{prize.image_filename}"


def _prize_to_response(prize: Prize) -> PrizeResponse:
    return PrizeResponse(
        id=prize.id,
        raffle_id=prize.raffle_id,
        name=prize.name,
        description=prize.description,
        order=prize.order,
        image_filename=prize.image_filename,
        image_url=_prize_image_url(prize),
    )


def _get_raffle_or_404(raffle_id: int, db: Session) -> Raffle:
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return raffle


@router.get("", response_model=list[PrizeResponse])
def list_prizes(raffle_id: int, db: Session = Depends(get_db)):
    _get_raffle_or_404(raffle_id, db)
    prizes = db.query(Prize).filter(Prize.raffle_id == raffle_id).order_by(Prize.order).all()
    return [_prize_to_response(p) for p in prizes]


@router.post("", response_model=PrizeResponse, status_code=201)
def create_prize(raffle_id: int, data: PrizeCreate, db: Session = Depends(get_db)):
    _get_raffle_or_404(raffle_id, db)
    prize = Prize(raffle_id=raffle_id, **data.model_dump())
    db.add(prize)
    db.commit()
    db.refresh(prize)
    return _prize_to_response(prize)


@router.patch("/{prize_id}", response_model=PrizeResponse)
def update_prize(raffle_id: int, prize_id: int, data: PrizeUpdate, db: Session = Depends(get_db)):
    prize = db.query(Prize).filter(Prize.id == prize_id, Prize.raffle_id == raffle_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prize, key, value)
    db.commit()
    db.refresh(prize)
    return _prize_to_response(prize)


@router.delete("/{prize_id}", status_code=204)
def delete_prize(raffle_id: int, prize_id: int, db: Session = Depends(get_db)):
    prize = db.query(Prize).filter(Prize.id == prize_id, Prize.raffle_id == raffle_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    if prize.image_filename:
        image_path = UPLOADS_DIR / prize.image_filename
        if image_path.exists():
            image_path.unlink()
    db.delete(prize)
    db.commit()


@router.post("/{prize_id}/image", response_model=PrizeResponse)
async def upload_prize_image(
    raffle_id: int,
    prize_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    prize = db.query(Prize).filter(Prize.id == prize_id, Prize.raffle_id == raffle_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="Premio no encontrado")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Usá JPG, PNG, WEBP o GIF.")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    if prize.image_filename:
        old_path = UPLOADS_DIR / prize.image_filename
        if old_path.exists():
            old_path.unlink()

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    dest = UPLOADS_DIR / filename
    dest.write_bytes(content)

    prize.image_filename = filename
    db.commit()
    db.refresh(prize)
    return _prize_to_response(prize)


@router.delete("/{prize_id}/image", response_model=PrizeResponse)
def delete_prize_image(raffle_id: int, prize_id: int, db: Session = Depends(get_db)):
    prize = db.query(Prize).filter(Prize.id == prize_id, Prize.raffle_id == raffle_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="Premio no encontrado")
    if prize.image_filename:
        image_path = UPLOADS_DIR / prize.image_filename
        if image_path.exists():
            image_path.unlink()
        prize.image_filename = None
        db.commit()
        db.refresh(prize)
    return _prize_to_response(prize)
