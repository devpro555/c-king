def detect_regime(df):
    spread = df["sma_20"] - df["sma_50"]
    vol = df["vol"].rolling(30).mean()
    if spread.mean() > 10 and vol.mean() < 0.02:
        return "uptrend"
    elif spread.mean() < -10:
        return "downtrend"
    elif vol.mean() > 0.05:
        return "volatile"
    else:
        return "sideways"