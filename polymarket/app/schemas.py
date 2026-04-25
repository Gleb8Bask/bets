from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.models import MarketStatus, OutcomeSide, TransactionType


# ── User ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    balance: float
    is_active: bool
    is_admin: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Market ────────────────────────────────────────────────────────

class MarketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    category: Optional[str] = Field(default=None, max_length=100)
    closes_at: Optional[datetime] = None


class MarketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    category: Optional[str] = Field(default=None, max_length=100)
    closes_at: Optional[datetime] = None
    status: Optional[MarketStatus] = None


class MarketResolve(BaseModel):
    outcome: OutcomeSide


class MarketOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    status: MarketStatus
    outcome: Optional[OutcomeSide]
    yes_price: float
    no_price: float
    yes_shares: float
    no_shares: float
    creator_id: Optional[int]
    created_at: datetime
    closes_at: Optional[datetime]
    resolved_at: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Position ──────────────────────────────────────────────────────

class PositionOut(BaseModel):
    id: int
    user_id: int
    market_id: int
    side: OutcomeSide
    shares: float
    avg_price: float
    total_cost: float
    is_winner: Optional[bool]
    payout: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    model_config = {"from_attributes": True}


# ── Trade ─────────────────────────────────────────────────────────

class BuyRequest(BaseModel):
    side: OutcomeSide
    amount: float = Field(gt=0, description="Dollar amount to spend")


class SellRequest(BaseModel):
    side: OutcomeSide
    amount: float = Field(gt=0, description="Number of shares to sell")


class TradeResponse(BaseModel):
    transaction: TransactionOut
    position: PositionOut
    market: MarketOut
    balance: float


# ── Transaction ───────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: int
    user_id: int
    market_id: Optional[int]
    type: TransactionType
    side: Optional[OutcomeSide]
    shares: Optional[float]
    price_per_share: Optional[float]
    amount: float
    balance_before: float
    balance_after: float
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Auth ──────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Wallet ────────────────────────────────────────────────────────

class DepositRequest(BaseModel):
    amount: float = Field(gt=0, le=100_000)


class WithdrawRequest(BaseModel):
    amount: float = Field(gt=0)


# ── Pagination ────────────────────────────────────────────────────

class PaginatedMarkets(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MarketOut]


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TransactionOut]


# Resolve forward refs
TradeResponse.model_rebuild()
