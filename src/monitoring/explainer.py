def explain_trade(signal, prob_up, row, settings):
    reasons = []
    if signal == "LONG":
        reasons.append(f"AI predicted {round(prob_up*100,1)}% chance of price going up.")
        if row["spread"] > settings["thresholds"]["spread_min"]:
            reasons.append("Trend strength confirmed by moving average spread.")
        if row["vol"] < settings["thresholds"]["vol_max"]:
            reasons.append("Volatility was low, reducing risk.")
        if 40 <= row["rsi"] <= 60:
            reasons.append(f"RSI was {round(row['rsi'],1)}, indicating neutral momentum.")
    elif signal == "SHORT":
        reasons.append(f"AI predicted {round((1-prob_up)*100,1)}% chance of price dropping.")
    else:
        reasons.append("No trade — conditions didn’t meet strategy thresholds.")
    return reasons