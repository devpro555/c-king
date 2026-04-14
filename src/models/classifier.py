import pandas as pd
from xgboost import XGBClassifier

class DirectionClassifier:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8
        )

    def prepare(self, df: pd.DataFrame):
        """Prepare features for training with enhanced indicators"""
        y = (df["close"].shift(-1) > df["close"]).astype(int)

        # Use all available technical indicators
        feature_cols = [
            "rsi", "atr", "vol", "sma_20", "sma_50", "ema_12", "ema_26",
            "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_position",
            "roc_5", "roc_10", "momentum", "close_std_10", "close_std_20",
            "vol_ratio", "pvt", "trend_slope", "spread",
            "high_low_ratio", "close_open_ratio"
        ]

        # Only use features that exist in the dataframe
        available_features = [col for col in feature_cols if col in df.columns]
        X = df[available_features]

        mask = ~y.isna()
        return X[mask], y[mask]

    def fit(self, df):
        X, y = self.prepare(df)
        self.model.fit(X, y)

    def predict_proba(self, df):
        """Enhanced prediction using all available features"""
        feature_cols = [
            "rsi", "atr", "vol", "sma_20", "sma_50", "ema_12", "ema_26",
            "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_position",
            "roc_5", "roc_10", "momentum", "close_std_10", "close_std_20",
            "vol_ratio", "pvt", "trend_slope", "spread",
            "high_low_ratio", "close_open_ratio"
        ]

        # Only use features that exist in the dataframe
        available_features = [col for col in feature_cols if col in df.columns]
        X = df[available_features].tail(1)

        if len(X) == 0:
            return 0.5  # Neutral prediction if no features available

        return float(self.model.predict_proba(X)[0, 1])