from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.db_migrate import run_migrations
from app.models import Ticket
from app.routers import auth, public, raffles, tickets
from app.services.ticket_urls import get_public_ticket_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
