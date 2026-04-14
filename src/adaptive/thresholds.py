def adjust_thresholds(equity, goal, days_left):
    target = goal["target_profit"]
    progress = equity - goal["starting_equity"]
    expected = target * (1 - days_left / goal["days"])
    
    # If we're behind on profit targets, be more aggressive with trading
    if progress < expected:
        return {"long_prob": 0.50, "risk_pct": 0.01}  # More aggressive signals
    
    # When ahead, be more conservative
    return {"long_prob": 0.58, "risk_pct": 0.007}