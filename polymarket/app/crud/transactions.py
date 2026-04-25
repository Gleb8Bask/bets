from sqlalchemy.orm import Session
from app.models import Transaction, TransactionType, OutcomeSide


def create(
    db: Session,
    user_id: int,
    type: TransactionType,
    amount: float,
    balance_before: float,
    balance_after: float,
    market_id: int | None = None,
    side: OutcomeSide | None = None,
    shares: float | None = None,
    price_per_share: float | None = None,
) -> Transaction:
    tx = Transaction(
        user_id=user_id,
        market_id=market_id,
        type=type,
        side=side,
        shares=shares,
        price_per_share=price_per_share,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
