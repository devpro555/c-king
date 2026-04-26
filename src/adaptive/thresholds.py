def adjust_thresholds(equity, goal, days_left):
    target = goal["target_profit"]
    progress = equity - goal["starting_equity"]
    expected = target * (1 - days_left / goal["days"])
    
    # CRITICAL FIX: Never lower thresholds when behind - this caused the losses!
    # Instead, reduce position size and be MORE selective
    if progress < expected:
        # Behind on targets: RAISE standards, not lower them
        return {"long_prob": 0.75, "risk_pct": 0.005}  # More selective, smaller size
    
    # When on track, maintain strict standards
    return {"long_prob": 0.75, "risk_pct": 0.005}