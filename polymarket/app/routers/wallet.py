from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, TransactionType
from app.schemas import UserOut, DepositRequest, WithdrawRequest
from app.auth.dependencies import get_current_active_user
from app.crud import users as crud_users
from app.crud import transactions as crud_transactions
from app.exceptions import InsufficientFundsError

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.post("/deposit", response_model=UserOut)
def deposit(
    payload: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    balance_before = current_user.balance
    current_user.balance += payload.amount

    crud_transactions.create(
        db,
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=payload.amount,
        balance_before=balance_before,
        balance_after=current_user.balance,
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/withdraw", response_model=UserOut)
def withdraw(
    payload: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.balance < payload.amount:
        raise InsufficientFundsError(
            balance=current_user.balance, required=payload.amount
        )

    balance_before = current_user.balance
    current_user.balance -= payload.amount

    crud_transactions.create(
        db,
        user_id=current_user.id,
        type=TransactionType.WITHDRAWAL,
        amount=payload.amount,
        balance_before=balance_before,
        balance_after=current_user.balance,
    )
    db.commit()
    db.refresh(current_user)
    return current_user
