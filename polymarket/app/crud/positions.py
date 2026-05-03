from sqlalchemy.orm import Session
from app.models import Position, OutcomeSide


def get_by_user(db: Session, user_id: int) -> list[Position]:
    return db.query(Position).filter(Position.user_id == user_id).all()


def get_by_user_market_side(
    db: Session, user_id: int, market_id: int, side: OutcomeSide
) -> Position | None:
    return (
        db.query(Position)
        .filter(
            Position.user_id == user_id,
            Position.market_id == market_id,
            Position.side == side,
        )
        .first()
    )


def upsert(
    db: Session,
    user_id: int,
    market_id: int,
    side: OutcomeSide,
    shares_delta: float,
    cost_delta: float,
) -> Position:
    """Add shares to an existing position, or create it if it doesn't exist."""
    position = get_by_user_market_side(db, user_id, market_id, side)

    if position is None:
        position = Position(
            user_id=user_id,
            market_id=market_id,
            side=side,
            shares=shares_delta,
            total_cost=cost_delta,
            avg_price=cost_delta / shares_delta if shares_delta > 0 else 0,
        )
        db.add(position)
    else:
        position.shares += shares_delta
        position.total_cost += cost_delta
        position.avg_price = (
            position.total_cost / position.shares if position.shares > 0 else 0
        )

    db.commit()
    db.refresh(position)
    return position


def reduce(
    db: Session,
    position: Position,
    shares_to_sell: float,
    proceeds: float,
) -> Position:
    """Remove shares from a position after a sell."""
    position.shares -= shares_to_sell
    position.total_cost -= proceeds
    if position.total_cost < 0:
        position.total_cost = 0
    db.commit()
    db.refresh(position)
    return position
