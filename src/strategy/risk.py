import math

def position_size(equity_usd: float, risk_pct: float, atr: float, tick_value: float = 1.0):
    risk_amount = equity_usd * risk_pct
    units = risk_amount / max(atr * tick_value, 1e-6)
    # Round to 4 decimal places instead of floor for crypto
    units = round(units, 4)
    # Ensure minimum position size for testnet (0.01 units)
    if units < 0.01:
        units = 0.01
    return units

def stops(entry_price: float, atr: float, direction: str, k=1.0):
    """
    Calculate stop loss and take profit with tighter risk control
    k=1.0 means stop loss at 1 ATR away (tighter than previous 1.5)
    """
    if direction == "LONG":
        stop_loss = entry_price - k * atr
        take_profit = entry_price + 2 * k * atr  # 2:1 reward-to-risk ratio
        return {"stop_loss": stop_loss, "take_profit": take_profit}
    if direction == "SHORT":
        stop_loss = entry_price + k * atr
        take_profit = entry_price - 2 * k * atr  # 2:1 reward-to-risk ratio
        return {"stop_loss": stop_loss, "take_profit": take_profit}
    return {"stop_loss": None, "take_profit": None}