"""
Constant-sum Automated Market Maker (AMM).

Prices are always:
  yes_price = yes_shares / (yes_shares + no_shares)
  no_price  = no_shares  / (yes_shares + no_shares)

They always sum to 1.0, like probabilities.

When someone BUYS yes with $X:
  - shares they receive = X / current_yes_price
  - yes_shares pool increases  → yes_price rises
  - no_shares pool unchanged   → no_price falls

When someone SELLS yes shares:
  - proceeds = shares * current_yes_price
  - yes_shares pool decreases  → yes_price falls
"""

from app.models import Market, OutcomeSide


def get_price(market: Market, side: OutcomeSide) -> float:
    total = market.yes_shares + market.no_shares
    if side == OutcomeSide.YES:
        return market.yes_shares / total
    return market.no_shares / total


def shares_for_amount(market: Market, side: OutcomeSide, amount: float) -> tuple[float, float]:
    """
    Calculate how many shares a dollar amount buys at the current price.
    Returns (shares, price_per_share).
    """
    price = get_price(market, side)
    shares = amount / price
    return shares, price


def proceeds_for_shares(market: Market, side: OutcomeSide, shares: float) -> tuple[float, float]:
    """
    Calculate dollar proceeds from selling a number of shares.
    Returns (proceeds, price_per_share).
    """
    price = get_price(market, side)
    proceeds = shares * price
    return proceeds, price


def update_prices(market: Market, side: OutcomeSide, shares_delta: float) -> Market:
    """
    Adjust share pools and recalculate cached prices after a trade.
    shares_delta > 0 for buys, < 0 for sells.
    """
    if side == OutcomeSide.YES:
        market.yes_shares += shares_delta
    else:
        market.no_shares += shares_delta

    total = market.yes_shares + market.no_shares
    market.yes_price = market.yes_shares / total
    market.no_price = market.no_shares / total
    return market
