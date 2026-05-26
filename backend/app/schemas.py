from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RaffleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    ticket_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_active: bool = True


class RaffleCreate(RaffleBase):
    pass


class RaffleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    ticket_price: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None


class RaffleResponse(RaffleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    ticket_count: int = 0
    paid_count: int = 0


class TicketBase(BaseModel):
    buyer_name: str = Field(..., min_length=1, max_length=200)
    buyer_phone: str | None = Field(None, max_length=30)
    buyer_email: EmailStr | None = None


class TicketCreate(TicketBase):
    raffle_id: int


class TicketUpdate(BaseModel):
    buyer_name: str | None = Field(None, min_length=1, max_length=200)
    buyer_phone: str | None = Field(None, max_length=30)
    buyer_email: EmailStr | None = None
    is_paid: bool | None = None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raffle_id: int
    ticket_number: str
    is_paid: bool
    created_at: datetime
    raffle_name: str | None = None


class SendTicketRequest(BaseModel):
    message: str | None = None


class WhatsAppLinkResponse(BaseModel):
    url: str
    message: str
