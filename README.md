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
git clone https://github.com/your-crypto-king.git
cd crypto-king
pip install -r requirements.txt


How to Run the Backend

1. Navigate to the project directory:
cd /Users/farazsiddiqui/Documents/development/c-king/crypto-king

2. Activate the virtual environment:
source venv/bin/activate

3. Run the FastAPI server:
PYTHONPATH=/Users/farazsiddiqui/Documents/development/c-king/crypto-king/src /Users/farazsiddiqui/Documents/development/c-king/crypto-king/venv/bin/python -m uvicorn src.app:app --host 0.0.0.0 --port 8002

How to kill
1. ps aux | grep "uvicorn src.app"
2. kill 60955 // 60955 will be the process id
