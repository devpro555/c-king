import os
import yaml


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ["1", "true", "yes", "y", "on"]


def _parse_float(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_settings(path=None):
    if path is None:
        # Try multiple possible locations
        possible_paths = [
            "config/settings.yaml",
            "../config/settings.yaml",
            os.path.join(os.path.dirname(__file__), "../config/settings.yaml")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                path = p
                break
        if path is None:
            raise FileNotFoundError("Could not find settings.yaml in any expected location")
    
    with open(path, "r") as f:
        settings = yaml.safe_load(f)

    settings["api_key"] = os.getenv("BINANCE_API_KEY", settings.get("api_key"))
    settings["api_secret"] = os.getenv("BINANCE_API_SECRET", settings.get("api_secret"))
    settings["testnet"] = _parse_bool(os.getenv("BINANCE_TESTNET"), settings.get("testnet", True))
    settings["starting_equity"] = _parse_float(os.getenv("STARTING_EQUITY"), settings.get("starting_equity", 1000.0))
    settings["risk_pct"] = _parse_float(os.getenv("RISK_PCT"), settings.get("risk_pct", 0.005))

    thresholds = settings.get("thresholds", {})
    thresholds["long_prob"] = _parse_float(os.getenv("THRESHOLD_LONG_PROB"), thresholds.get("long_prob", 0.6))
    thresholds["short_prob"] = _parse_float(os.getenv("THRESHOLD_SHORT_PROB"), thresholds.get("short_prob", 0.4))
    thresholds["spread_min"] = _parse_float(os.getenv("THRESHOLD_SPREAD_MIN"), thresholds.get("spread_min", 10.0))
    thresholds["vol_max"] = _parse_float(os.getenv("THRESHOLD_VOL_MAX"), thresholds.get("vol_max", 0.1))
    settings["thresholds"] = thresholds

    return settings
