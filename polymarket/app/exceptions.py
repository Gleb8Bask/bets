from fastapi import HTTPException, status


class InsufficientFundsError(HTTPException):
    def __init__(self, balance: float, required: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds — balance ${balance:.2f}, required ${required:.2f}",
        )


class MarketClosedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This market is closed and no longer accepting trades",
        )


class MarketAlreadyResolvedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This market has already been resolved",
        )


class MarketNotFoundError(HTTPException):
    def __init__(self, market_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market {market_id} not found",
        )


class UserNotFoundError(HTTPException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )


class PositionNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a position on this side of the market",
        )


class NotEnoughSharesError(HTTPException):
    def __init__(self, owned: float, requested: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough shares — you own {owned:.4f}, tried to sell {requested:.4f}",
        )
