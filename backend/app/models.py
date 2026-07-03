import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Raffle(Base):
    __tablename__ = "raffles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ticket_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    draw_closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_tickets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="raffle", cascade="all, delete-orphan")
    prizes: Mapped[list["Prize"]] = relationship("Prize", back_populates="raffle", cascade="all, delete-orphan", order_by="Prize.order")


class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raffle_id: Mapped[int] = mapped_column(ForeignKey("raffles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    raffle: Mapped["Raffle"] = relationship("Raffle", back_populates="prizes")


class DrawResult(Base):
    __tablename__ = "draw_results"
    __table_args__ = (UniqueConstraint("raffle_id", "prize_id", name="uq_draw_raffle_prize"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raffle_id: Mapped[int] = mapped_column(ForeignKey("raffles.id", ondelete="CASCADE"), nullable=False)
    prize_id: Mapped[int] = mapped_column(ForeignKey("prizes.id", ondelete="CASCADE"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    drawn_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    raffle: Mapped["Raffle"] = relationship("Raffle")
    prize: Mapped["Prize"] = relationship("Prize")
    ticket: Mapped["Ticket"] = relationship("Ticket")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (UniqueConstraint("raffle_id", "ticket_number", name="uq_raffle_ticket_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    short_code: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    raffle_id: Mapped[int] = mapped_column(ForeignKey("raffles.id", ondelete="CASCADE"), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(20), nullable=False)
    buyer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    buyer_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    buyer_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_proof_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_proof_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    raffle: Mapped["Raffle"] = relationship("Raffle", back_populates="tickets")
