import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Ticket
from app.routers import auth, draws, public, prizes, raffles, tickets
from app.services.ticket_urls import get_public_ticket_url

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/ root
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "prizes").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "raffles").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "payment-proofs").mkdir(parents=True, exist_ok=True)


def run_migrations() -> None:
    """Apply all pending Alembic migrations at startup."""
    ini_path = BASE_DIR / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    # Ensure the script location is always resolved relative to alembic.ini
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    logger.info("Running Alembic migrations…")
    alembic_command.upgrade(cfg, "head")
    logger.info("Migrations complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(
    title="La Rifa API",
    description="API para gestión de sorteos y tickets",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(raffles.router)
app.include_router(tickets.router)
app.include_router(prizes.router)
app.include_router(draws.router)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/s/{short_code}")
def redirect_short_url(short_code: str, db: Session = Depends(get_db)):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.short_code == short_code, Ticket.is_paid.is_(True))
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Enlace no válido")
    return RedirectResponse(url=get_public_ticket_url(ticket), status_code=302)
