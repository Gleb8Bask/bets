from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserOut, UserUpdate, PositionOut, TransactionOut, PaginatedTransactions
from app.auth.dependencies import get_current_active_user
from app.auth.hashing import hash_password
from app.crud import positions as crud_positions
from app.crud import transactions as crud_transactions

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if payload.email:
        current_user.email = payload.email
    if payload.username:
        current_user.username = payload.username
    if payload.password:
        current_user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/positions", response_model=list[PositionOut])
def get_my_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    positions = crud_positions.get_by_user(db, current_user.id)
    # Attach current market value to each position
    result = []
    for pos in positions:
        market = pos.market
        total = market.yes_shares + market.no_shares
        price = market.yes_shares / total if pos.side.value == "yes" else market.no_shares / total
        current_value = pos.shares * price
        pnl = current_value - pos.total_cost

        pos_dict = {
            **pos.__dict__,
            "current_value": round(current_value, 4),
            "unrealized_pnl": round(pnl, 4),
        }
        result.append(PositionOut.model_validate(pos_dict))
    return result


@router.get("/me/transactions", response_model=PaginatedTransactions)
def get_my_transactions(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    skip = (page - 1) * page_size
    txs = crud_transactions.get_by_user(db, current_user.id, skip=skip, limit=page_size)
    return PaginatedTransactions(
        total=len(txs),
        page=page,
        page_size=page_size,
        items=txs,
    )
