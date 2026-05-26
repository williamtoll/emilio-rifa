from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.phone import normalize_paraguay_phone


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
    buyer_phone: str | None = Field(
        None,
        max_length=10,
        description="Móvil Paraguay: 09XXXXXXXX",
        examples=["0961732207"],
    )
    buyer_email: EmailStr | None = None

    @field_validator("buyer_phone")
    @classmethod
    def validate_paraguay_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        return normalize_paraguay_phone(value)


class TicketCreate(TicketBase):
    raffle_id: int


class TicketUpdate(BaseModel):
    buyer_name: str | None = Field(None, min_length=1, max_length=200)
    buyer_phone: str | None = Field(None, max_length=10, examples=["0961732207"])
    buyer_email: EmailStr | None = None
    is_paid: bool | None = None

    @field_validator("buyer_phone")
    @classmethod
    def validate_paraguay_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        return normalize_paraguay_phone(value)


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    public_url: str | None = None
    raffle_id: int
    ticket_number: str
    is_paid: bool
    created_at: datetime
    raffle_name: str | None = None


class PublicTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    ticket_number: str
    buyer_name: str
    raffle_name: str
    ticket_price: Decimal
    is_paid: bool


class SendTicketRequest(BaseModel):
    message: str | None = None


class WhatsAppLinkResponse(BaseModel):
    url: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str
