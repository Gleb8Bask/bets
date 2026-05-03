from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Enum, Text, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    pass


class MarketStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class OutcomeSide(str, enum.Enum):
    YES = "yes"
    NO = "no"


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYOUT = "payout"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    positions = relationship("Position", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    markets_created = relationship("Market", back_populates="creator")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="non_negative_balance"),
    )


class Market(Base):
    __tablename__ = "markets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    status = Column(Enum(MarketStatus), nullable=False, default=MarketStatus.OPEN)
    outcome = Column(Enum(OutcomeSide), nullable=True)
    yes_shares = Column(Float, nullable=False, default=100.0)
    no_shares = Column(Float, nullable=False, default=100.0)
    yes_price = Column(Float, nullable=False, default=0.5)
    no_price = Column(Float, nullable=False, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closes_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("User", back_populates="markets_created")
    positions = relationship("Position", back_populates="market")
    transactions = relationship("Transaction", back_populates="market")

    __table_args__ = (
        CheckConstraint("yes_shares > 0", name="positive_yes_shares"),
        CheckConstraint("no_shares > 0", name="positive_no_shares"),
    )


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False, index=True)
    side = Column(Enum(OutcomeSide), nullable=False)
    shares = Column(Float, nullable=False, default=0.0)
    avg_price = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    is_winner = Column(Boolean, nullable=True)
    payout = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="positions")
    market = relationship("Market", back_populates="positions")

    __table_args__ = (
        CheckConstraint("shares >= 0", name="non_negative_shares"),
        UniqueConstraint("user_id", "market_id", "side", name="uq_positions_user_market_side"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=True)
    type = Column(Enum(TransactionType), nullable=False)
    side = Column(Enum(OutcomeSide), nullable=True)
    shares = Column(Float, nullable=True)
    price_per_share = Column(Float, nullable=True)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    market = relationship("Market", back_populates="transactions")
