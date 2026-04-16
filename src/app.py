from fastapi import FastAPI
from pydantic import BaseModel
from src.strategy.executor import TradingExecutor
from src.utils.config import load_settings
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = FastAPI()
settings = load_settings()
executor = TradingExecutor(settings)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

class Goal(BaseModel):
    target_profit: float
    days: int
    max_drawdown_pct: float = 5.0
    risk_level: str = "moderate"

class ModeRequest(BaseModel):
    mode: str

def trading_cycle():
    """Run trading analysis for all symbols configured"""
    executor.log("--- Starting trading cycle ---")
    for symbol in executor.settings["symbols"]:
        try:
            executor.step(symbol)
        except Exception as e:
            executor.log(f"Error processing {symbol}: {str(e)}", "ERROR")
    executor.log("--- Completed trading cycle ---")

@app.post("/plan")
def create_plan(goal: Goal):
    plan = executor.create_goal_plan(goal)
    return {"plan": plan}

@app.post("/start")
def start_trading():
    executor.start()
    # Run trading cycle immediately
    trading_cycle()
    # Schedule trading cycle every 5 minutes (300 seconds)
    scheduler.add_job(trading_cycle, 'interval', seconds=300, id='trading_cycle', replace_existing=True)
    executor.log("Scheduled trading cycle to run every 5 minutes")
    return {"status": "running", "message": "Trading started! Running analysis immediately and every 5 minutes"}

@app.post("/stop")
def stop_trading():
    executor.stop()
    # Remove the scheduled job
    try:
        scheduler.remove_job('trading_cycle')
        executor.log("Trading cycle job removed from scheduler")
    except:
        pass
    return {"status": "stopped", "message": "Trading cycle stopped"}

@app.get("/status")
def status():
    return executor.status()

@app.post("/set-mode")
def set_mode(request: ModeRequest):
    executor.settings["mode"] = request.mode
    return {"mode": request.mode}

@app.get("/trades")
def get_trades():
    return executor.trade_log[-20:]

@app.get("/explain")
def explain_trade(trade_id: str):
    for t in executor.trade_log:
        if t.get("id") == trade_id:
            explanation = t.get("explanation", [])
            
            # Handle both list and string formats
            if isinstance(explanation, str):
                reasons = explanation.split(" | ") if explanation else []
            else:
                reasons = explanation if isinstance(explanation, list) else []
            
            # Add profit/loss analysis for closed trades
            if t.get("status") == "closed" and "exit_price" in t:
                pnl = t.get("pnl", 0)
                entry_price = t.get("entry_price", 0)
                exit_price = t.get("exit_price", 0)
                side = t.get("side", "")
                
                # Calculate price movement and expected vs actual
                price_change_pct = ((exit_price - entry_price) / entry_price) * 100
                
                if side == "LONG":
                    # LONG profits when price goes up
                    expected_direction = "up"
                    actual_direction = "up" if exit_price > entry_price else "down"
                    profitable = pnl > 0
                else:  # SHORT
                    # SHORT profits when price goes down
                    expected_direction = "down"
                    actual_direction = "down" if exit_price < entry_price else "up"
                    profitable = pnl > 0
                
                # Add P&L details
                pnl_text = f"Trade P&L: ${pnl:.2f} ({price_change_pct:+.2f}%)"
                if profitable:
                    pnl_text += f" - PROFITABLE: Price moved {actual_direction} as expected"
                else:
                    pnl_text += f" - LOSS: Price moved {actual_direction} but expected {expected_direction}"
                
                reasons.append(pnl_text)
                reasons.append(f"Entry: ${entry_price:.2f} → Exit: ${exit_price:.2f}")
                
                # Calculate duration if available
                if t.get("entry_time") and t.get("exit_time"):
                    try:
                        entry_dt = datetime.fromisoformat(t["entry_time"])
                        exit_dt = datetime.fromisoformat(t["exit_time"])
                        duration = exit_dt - entry_dt
                        hours = duration.total_seconds() / 3600
                        reasons.append(f"Duration: {hours:.1f} hours")
                    except:
                        pass
            
            return reasons
    return []

@app.get("/logs")
def get_logs(limit: int = 100):
    return executor.logs[-limit:]

@app.get("/performance")
def get_performance():
    return executor.get_performance_summary()

@app.get("/positions")
def get_positions():
    return {
        "open_positions": executor.open_positions,
        "position_count": len(executor.open_positions)
    }

@app.post("/close-position/{symbol}")
def close_position(symbol: str):
    """Manually close a position"""
    if symbol not in executor.open_positions:
        return {"error": f"No open position for {symbol}"}
    
    # Get current price
    try:
        ticker = executor.client.fetch_ticker(symbol)
        current_price = ticker["last"]
        executor.close_position(symbol, current_price)
        return {"message": f"Position closed for {symbol}"}
    except Exception as e:
        return {"error": f"Failed to close position: {str(e)}"}