import numpy as np
import pandas as pd

def rsi(close: pd.Series, period=14):
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/period).mean()
    down = -delta.clip(upper=0).ewm(alpha=1/period).mean()
    rs = up / (down + 1e-12)
    return 100 - (100 / (1 + rs))

def atr(high, low, close, period=14):
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
    return pd.Series(tr).ewm(alpha=1/period).mean()

import numpy as np
import pandas as pd

def rsi(close: pd.Series, period=14):
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/period).mean()
    down = -delta.clip(upper=0).ewm(alpha=1/period).mean()
    rs = up / (down + 1e-12)
    return 100 - (100 / (1 + rs))

def atr(high, low, close, period=14):
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
    return pd.Series(tr).ewm(alpha=1/period).mean()

def macd(close, fast=12, slow=26, signal=9):
    """MACD indicator"""
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger_bands(close, period=20, std_dev=2):
    """Bollinger Bands"""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def volume_indicators(volume, close):
    """Volume-based indicators"""
    # Volume moving averages
    vol_sma_10 = volume.rolling(10).mean()
    vol_sma_20 = volume.rolling(20).mean()

    # Volume ratio
    vol_ratio = volume / vol_sma_20.replace(0, 1)

    # Price-volume trend
    pvt = ((close - close.shift(1)) / close.shift(1).replace(0, 1)) * volume
    pvt_cumsum = pvt.cumsum()

    return vol_ratio, pvt_cumsum

def regime_features(df):
    """Enhanced feature engineering for better predictions"""
    # Basic indicators
    df["rsi"] = rsi(df["close"])
    df["atr"] = atr(df["high"], df["low"], df["close"])
    df["vol"] = df["close"].pct_change().rolling(30).std()

    # Trend indicators
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["ema_12"] = df["close"].ewm(span=12).mean()
    df["ema_26"] = df["close"].ewm(span=26).mean()

    # MACD
    df["macd_line"], df["macd_signal"], df["macd_hist"] = macd(df["close"])

    # Bollinger Bands
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = bollinger_bands(df["close"])
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # Momentum indicators
    df["roc_5"] = df["close"].pct_change(5)  # 5-period rate of change
    df["roc_10"] = df["close"].pct_change(10)  # 10-period rate of change
    df["momentum"] = df["close"] - df["close"].shift(10)

    # Volatility indicators
    df["close_std_10"] = df["close"].rolling(10).std()
    df["close_std_20"] = df["close"].rolling(20).std()

    # Volume indicators (if volume data available)
    if "volume" in df.columns:
        df["vol_ratio"], df["pvt"] = volume_indicators(df["volume"], df["close"])
    else:
        df["vol_ratio"] = 1.0
        df["pvt"] = 0.0

    # Trend strength
    df["trend_slope"] = df["sma_20"].diff()
    df["spread"] = df["sma_20"] - df["sma_50"]

    # Price action features
    df["high_low_ratio"] = df["high"] / df["low"]
    df["close_open_ratio"] = df["close"] / df["open"]

    return df.dropna()