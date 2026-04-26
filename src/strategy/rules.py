def ensemble_signal(prob_up: float, df_row, thresholds):
    """
    Generate balanced LONG/SHORT signals with trend awareness and ensemble logic
    """
    # CRITICAL FIX: Increase thresholds to prevent overconfident trades
    # Only take high-conviction signals: 75%+ for LONG, 25%- for SHORT
    long_signal = prob_up > 0.75   # Need 75%+ confidence for LONG
    short_signal = prob_up < 0.25  # Need <25% confidence for SHORT (very strong down prediction)

    # Ensemble factors for additional confirmation
    ensemble_score = 0

    try:
        # Trend confirmation
        trend_up = df_row.get("sma_20", 0) > df_row.get("sma_50", 0)
        trend_down = df_row.get("sma_20", 0) < df_row.get("sma_50", 0)

        # Momentum confirmation
        rsi = df_row.get("rsi", 50)
        momentum_up = rsi > 55
        momentum_down = rsi < 45

        # MACD confirmation
        macd_hist = df_row.get("macd_hist", 0)
        macd_up = macd_hist > 0
        macd_down = macd_hist < 0

        # Bollinger Band position
        bb_position = df_row.get("bb_position", 0.5)
        bb_upper = bb_position > 0.8  # Price near upper band
        bb_lower = bb_position < 0.2  # Price near lower band

        # CRITICAL: Strict volatility filter - skip choppy markets
        vol_ok = df_row.get("vol", 0) < thresholds.get("vol_max", 0.05)  # Reduced threshold from 0.1 to 0.05

        if not vol_ok:
            return "FLAT"  # Skip if too volatile - avoid whipsaws

        # Build ensemble score
        if long_signal:
            ensemble_score += 2  # Strong AI signal
            if trend_up: ensemble_score += 1
            if momentum_up: ensemble_score += 1
            if macd_up: ensemble_score += 1
            if bb_lower: ensemble_score += 0.5  # Potential bounce from lower band

            if ensemble_score >= 4.5:  # CRITICAL: Raise bar to 4.5+ for LONG (need strong confirmation)
                return "LONG"

        elif short_signal:
            ensemble_score += 2  # Strong AI signal
            if trend_down: ensemble_score += 1
            if momentum_down: ensemble_score += 1
            if macd_down: ensemble_score += 1
            if bb_upper: ensemble_score += 0.5  # Potential rejection from upper band

            if ensemble_score >= 4.5:  # CRITICAL: Raise bar to 4.5+ for SHORT (need strong confirmation)
                return "SHORT"

    except Exception as e:
        # Fallback to simple probability-based signals if ensemble fails
        if long_signal:
            return "LONG"
        elif short_signal:
            return "SHORT"

    return "FLAT"