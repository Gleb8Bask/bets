from sqlalchemy.orm import Session
from app.models import Market, Position, OutcomeSide, TransactionType
from app.crud import transactions as crud_transactions


def settle_market(db: Session, market: Market) -> list[Position]:
    """
    After a market is resolved, pay out all winning positions.
    Each winning share is worth $1.00.
    Returns list of winning positions that were paid out.
    """
    if market.outcome is None:
        raise ValueError("Market has no outcome set")

    winning_side = market.outcome
    positions = db.query(Position).filter(Position.market_id == market.id).all()
    paid_out = []

    for position in positions:
        is_winner = position.side == winning_side
        position.is_winner = is_winner

        if is_winner and position.shares > 0:
            payout = position.shares * 1.0  # each winning share = $1

            balance_before = position.user.balance
            position.user.balance += payout
            position.payout = payout

            crud_transactions.create(
                db,
                user_id=position.user_id,
                market_id=market.id,
                type=TransactionType.PAYOUT,
                side=position.side,
                shares=position.shares,
                price_per_share=1.0,
                amount=payout,
                balance_before=balance_before,
                balance_after=position.user.balance,
            )
            paid_out.append(position)
        else:
            position.payout = 0.0

    db.commit()
    return paid_out
