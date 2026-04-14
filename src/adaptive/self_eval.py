def evaluate_performance(trades):
    total = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    drawdowns = [t["drawdown"] for t in trades]
    win_rate = wins / total if total > 0 else 0
    max_dd = max(drawdowns) if drawdowns else 0
    if win_rate < 0.5 or max_dd > 5:
        return "pause"
    return "continue"