# Crypto King — Halal AI Spot Trading Bot

A fully configurable, goal-driven, halal-compliant crypto trading system powered by AI.

## Features
- Spot-only trading (no futures, no leverage)
- AI strategy engine (XGBoost + regime filters)
- Goal planner (e.g. “Make $150 in 20 days”)
- Risk manager (position sizing, stop-loss, drawdown cap)
- Trade explainer (plain language reasons for each trade)
- FastAPI backend + optional Flutter dashboard
- Paper trading via Binance testnet

## Setup

```bash
git clone https://github.com/devpro555/c-king.git
cd crypto-king
pip install -r requirements.txt
```

### How to Run the Backend Locally

1. Navigate to the project directory:

```bash
cd /Users/farazsiddiqui/Documents/development/c-king/crypto-king
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Run the FastAPI server:

```bash
PYTHONPATH=src uvicorn src.app:app --host 0.0.0.0 --port 8002
```

### Environment Variables

The backend supports sensitive values through environment variables instead of storing them in `config/settings.yaml`.

- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`
- `BINANCE_TESTNET` (`true` or `false`)
- `DATABASE_URL` (Railway MySQL connection string)
- `STARTING_EQUITY`
- `RISK_PCT`
- `THRESHOLD_LONG_PROB`
- `THRESHOLD_SHORT_PROB`
- `THRESHOLD_SPREAD_MIN`
- `THRESHOLD_VOL_MAX`

### Railway Deployment Notes

Railway should use the service root `crypto-king` and the `Procfile` entry:

```bash
web: sh -lc 'uvicorn src.app:app --host 0.0.0.0 --port $PORT'
```

Railway will automatically provide `PORT`, and you should also set the database connection string under `DATABASE_URL`.

### How to stop the backend

```bash
ps aux | grep "uvicorn src.app"
kill <pid>
```