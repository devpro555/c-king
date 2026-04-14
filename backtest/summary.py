def summarize_performance(trades):
    total = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    losses = total - wins
    win_rate = round(wins / total * 100, 2)
    pnl_total = round(sum(t["pnl"] for t in trades), 2)
    max_dd = round(max(t["drawdown"] for t in trades), 2)
    print(f"Trades: {total} | Wins: {wins} | Win Rate: {win_rate}%")
    print(f"Total P&L: ${pnl_total} | Max Drawdown: {max_dd}%")