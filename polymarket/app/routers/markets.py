from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, MarketStatus
from app.schemas import (
    MarketCreate, MarketUpdate, MarketResolve, MarketOut,
    BuyRequest, SellRequest, TradeResponse, PaginatedMarkets,
)
from app.auth.dependencies import get_current_active_user, require_admin
from app.crud import markets as crud_markets
from app.services import trading, settlement
from app.exceptions import MarketNotFoundError

router = APIRouter(prefix="/markets", tags=["Markets"])


def _get_market_or_404(db: Session, market_id: int):
    market = crud_markets.get_by_id(db, market_id)
    if not market:
        raise MarketNotFoundError(market_id)
    return market


@router.get("/", response_model=PaginatedMarkets)
def list_markets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: MarketStatus | None = None,
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_markets.get_all(db, skip=skip, limit=page_size, status=status)
    return PaginatedMarkets(total=total, page=page, page_size=page_size, items=items)


@router.get("/{market_id}", response_model=MarketOut)
def get_market(market_id: int, db: Session = Depends(get_db)):
    return _get_market_or_404(db, market_id)


@router.post("/", response_model=MarketOut, status_code=201)
def create_market(
    payload: MarketCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return crud_markets.create(
        db,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        closes_at=payload.closes_at,
        creator_id=admin.id,
    )


@router.patch("/{market_id}", response_model=MarketOut)
def update_market(
    market_id: int,
    payload: MarketUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    market = _get_market_or_404(db, market_id)
    return crud_markets.update(db, market, **payload.model_dump(exclude_none=True))


@router.post("/{market_id}/resolve", response_model=MarketOut)
def resolve_market(
    market_id: int,
    payload: MarketResolve,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    market = _get_market_or_404(db, market_id)
    if market.status == MarketStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Market already resolved")
    market = crud_markets.resolve(db, market, payload.outcome)
    settlement.settle_market(db, market)
    return market


@router.post("/{market_id}/buy", response_model=TradeResponse)
def buy(
    market_id: int,
    payload: BuyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    market = _get_market_or_404(db, market_id)
    transaction, position, market = trading.execute_buy(
        db, current_user, market, payload.side, payload.amount
    )
    return TradeResponse(
        transaction=transaction,
        position=position,
        market=market,
        balance=current_user.balance,
    )


@router.post("/{market_id}/sell", response_model=TradeResponse)
def sell(
    market_id: int,
    payload: SellRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    market = _get_market_or_404(db, market_id)
    transaction, position, market = trading.execute_sell(
        db, current_user, market, payload.side, payload.amount
    )
    return TradeResponse(
        transaction=transaction,
        position=position,
        market=market,
        balance=current_user.balance,
    )
