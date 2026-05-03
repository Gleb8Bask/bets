from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Market, MarketStatus, OutcomeSide


def get_all(db: Session, skip: int = 0, limit: int = 20, status: MarketStatus | None = None):
    q = db.query(Market)
    if status:
        q = q.filter(Market.status == status)
    total = q.count()
    items = q.order_by(Market.created_at.desc()).offset(skip).limit(limit).all()
    return total, items


def get_by_id(db: Session, market_id: int) -> Market | None:
    return db.query(Market).filter(Market.id == market_id).first()


def create(db: Session, title: str, description: str | None, category: str | None,
           closes_at: datetime | None, creator_id: int | None) -> Market:
    market = Market(
        title=title,
        description=description,
        category=category,
        closes_at=closes_at,
        creator_id=creator_id,
    )
    db.add(market)
    db.commit()
    db.refresh(market)
    return market


def update(db: Session, market: Market, **kwargs) -> Market:
    for key, value in kwargs.items():
        if value is not None:
            setattr(market, key, value)
    db.commit()
    db.refresh(market)
    return market


def resolve(db: Session, market: Market, outcome: OutcomeSide) -> Market:
    market.outcome = outcome
    market.status = MarketStatus.RESOLVED
    market.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(market)
    return market
