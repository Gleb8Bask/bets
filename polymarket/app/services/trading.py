from sqlalchemy.orm import Session

from app.models import Market, User, MarketStatus, TransactionType, OutcomeSide
from app.exceptions import (
    MarketClosedError, MarketAlreadyResolvedError,
    InsufficientFundsError, PositionNotFoundError, NotEnoughSharesError,
)
from app.services import pricing
from app.crud import positions as crud_positions
from app.crud import transactions as crud_transactions


def _assert_market_open(market: Market):
    if market.status == MarketStatus.RESOLVED:
        raise MarketAlreadyResolvedError()
    if market.status in (MarketStatus.CLOSED, MarketStatus.CANCELLED):
        raise MarketClosedError()


def execute_buy(
    db: Session,
    user: User,
    market: Market,
    side: OutcomeSide,
    amount: float,
):
    """
    Buy `amount` dollars worth of shares on `side`.
    Returns (transaction, position, updated_market).
    """
    _assert_market_open(market)

    if user.balance < amount:
        raise InsufficientFundsError(balance=user.balance, required=amount)

    shares, price = pricing.shares_for_amount(market, side, amount)

    # Update user balance
    balance_before = user.balance
    user.balance -= amount

    # Update market share pools + prices
    pricing.update_prices(market, side, shares_delta=+shares)

    # Upsert position
    position = crud_positions.upsert(
        db, user.id, market.id, side,
        shares_delta=shares,
        cost_delta=amount,
    )

    # Record transaction
    transaction = crud_transactions.create(
        db,
        user_id=user.id,
        market_id=market.id,
        type=TransactionType.BUY,
        side=side,
        shares=shares,
        price_per_share=price,
        amount=amount,
        balance_before=balance_before,
        balance_after=user.balance,
    )

    db.commit()
    db.refresh(user)
    db.refresh(market)
    db.refresh(position)
    db.refresh(transaction)

    return transaction, position, market


def execute_sell(
    db: Session,
    user: User,
    market: Market,
    side: OutcomeSide,
    shares_to_sell: float,
):
    """
    Sell `shares_to_sell` shares on `side`.
    Returns (transaction, position, updated_market).
    """
    _assert_market_open(market)

    position = crud_positions.get_by_user_market_side(db, user.id, market.id, side)
    if position is None or position.shares <= 0:
        raise PositionNotFoundError()
    if position.shares < shares_to_sell:
        raise NotEnoughSharesError(owned=position.shares, requested=shares_to_sell)

    proceeds, price = pricing.proceeds_for_shares(market, side, shares_to_sell)

    # Update user balance
    balance_before = user.balance
    user.balance += proceeds

    # Update market share pools + prices
    pricing.update_prices(market, side, shares_delta=-shares_to_sell)

    # Reduce position
    position = crud_positions.reduce(db, position, shares_to_sell, proceeds)

    # Record transaction
    transaction = crud_transactions.create(
        db,
        user_id=user.id,
        market_id=market.id,
        type=TransactionType.SELL,
        side=side,
        shares=shares_to_sell,
        price_per_share=price,
        amount=proceeds,
        balance_before=balance_before,
        balance_after=user.balance,
    )

    db.commit()
    db.refresh(user)
    db.refresh(market)
    db.refresh(position)
    db.refresh(transaction)

    return transaction, position, market
