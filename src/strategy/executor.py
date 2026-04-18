import pandas as pd
import logging
import time
from datetime import datetime
from sqlalchemy.exc import OperationalError
from src.exchange.binance import BinanceClient
from src.features.indicators import regime_features
from src.models.classifier import DirectionClassifier
from src.strategy.rules import ensemble_signal
from src.strategy.risk import position_size, stops
from src.monitoring.explainer import explain_trade
from src.adaptive.regime import detect_regime
from src.adaptive.thresholds import adjust_thresholds
from src.database.models import Trade, SystemState, LogEntry, OpenPosition, init_db, get_db

class TradingExecutor:
    def __init__(self, settings):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.client = BinanceClient(settings["api_key"], settings["api_secret"], settings["testnet"])
        self.db_initialized = False
        self.trade_log = []
        self.open_positions = {}
        self.state = {"equity": settings.get("starting_equity", 1000), "virtual_mode": True}
        self.running = False

        self.model = DirectionClassifier()
        self.goal = {
            "target_profit": 150,
            "days": 20,
            "starting_equity": self.state["equity"]
        }
        self.elapsed_days = 0
        self.logger.info("TradingExecutor created; database initialization deferred")

    def initialize_database(self, retries=6, delay=5):
        if self.db_initialized:
            return

        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                init_db()
                self.load_from_database()
                self.db_initialized = True
                self.logger.info("Database initialized and loaded successfully")
                return
            except OperationalError as exc:
                last_exception = exc
                self.logger.warning(
                    f"Database not ready yet (attempt {attempt}/{retries}). "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            except Exception as exc:
                self.logger.error("Unexpected database initialization error", exc_info=True)
                raise

        raise RuntimeError(
            "Database initialization failed after "
            f"{retries} attempts.",
        ) from last_exception

    def load_from_database(self):
        """Load all data from database on startup"""
        db = get_db()

        # Load system state
        system_state = db.query(SystemState).filter(SystemState.id == 1).first()
        if system_state:
            self.state = {
                "equity": system_state.equity,
                "virtual_mode": system_state.virtual_mode
            }
            self.running = system_state.running
        else:
            # Create default system state
            self.state = {"equity": self.settings.get("starting_equity", 1000), "virtual_mode": True}
            self.running = False
            default_state = SystemState(
                equity=self.state["equity"],
                running=self.running,
                virtual_mode=self.state["virtual_mode"]
            )
            db.add(default_state)
            db.commit()

        # Load trades
        self.trade_log = []
        trades = db.query(Trade).order_by(Trade.entry_time.desc()).limit(100).all()
        for trade in trades:
            self.trade_log.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "signal": trade.signal,
                "side": trade.side,
                "size": trade.size,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": trade.pnl,
                "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "status": trade.status,
                "explanation": trade.explanation.split('|') if trade.explanation else [],
                "reason": trade.reason
            })

        # Load open positions
        self.open_positions = {}
        positions = db.query(OpenPosition).filter(OpenPosition.status == 'open').all()
        for pos in positions:
            self.open_positions[pos.symbol] = {
                "symbol": pos.symbol,
                "side": pos.side,
                "size": pos.size,
                "entry_price": pos.entry_price,
                "stop_loss": pos.stop_loss,
                "take_profit": pos.take_profit,
                "entry_time": pos.entry_time,
                "status": pos.status
            }

        # Load recent logs
        self.logs = []
        logs = db.query(LogEntry).order_by(LogEntry.timestamp.desc()).limit(200).all()
        for log in logs:
            self.logs.append({
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message
            })

        db.close()

    def load_from_database(self):
        """Load all data from database on startup"""
        db = get_db()

        # Load system state
        system_state = db.query(SystemState).filter(SystemState.id == 1).first()
        if system_state:
            self.state = {
                "equity": system_state.equity,
                "virtual_mode": system_state.virtual_mode
            }
            self.running = system_state.running
        else:
            # Create default system state
            self.state = {"equity": self.settings.get("starting_equity", 1000), "virtual_mode": True}
            self.running = False
            default_state = SystemState(
                equity=self.state["equity"],
                running=self.running,
                virtual_mode=self.state["virtual_mode"]
            )
            db.add(default_state)
            db.commit()

        # Load trades
        self.trade_log = []
        trades = db.query(Trade).order_by(Trade.entry_time.desc()).limit(100).all()
        for trade in trades:
            self.trade_log.append({
                "id": trade.id,
                "symbol": trade.symbol,
                "signal": trade.signal,
                "side": trade.side,
                "size": trade.size,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": trade.pnl,
                "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "status": trade.status,
                "explanation": trade.explanation.split('|') if trade.explanation else [],
                "reason": trade.reason
            })

        # Load open positions
        self.open_positions = {}
        positions = db.query(OpenPosition).filter(OpenPosition.status == 'open').all()
        for pos in positions:
            self.open_positions[pos.symbol] = {
                "symbol": pos.symbol,
                "side": pos.side,
                "size": pos.size,
                "entry_price": pos.entry_price,
                "stop_loss": pos.stop_loss,
                "take_profit": pos.take_profit,
                "entry_time": pos.entry_time,
                "status": pos.status
            }

        # Load recent logs
        self.logs = []
        logs = db.query(LogEntry).order_by(LogEntry.timestamp.desc()).limit(200).all()
        for log in logs:
            self.logs.append({
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message
            })

        db.close()

    def log(self, message, level="INFO"):
        timestamp = datetime.now()
        log_entry = {"timestamp": timestamp.isoformat(), "level": level, "message": message}
        self.logs.append(log_entry)

        # Save to database
        db = get_db()
        db_log = LogEntry(timestamp=timestamp, level=level, message=message)
        db.add(db_log)
        db.commit()
        db.close()

        self.logger.info(message)

    def open_position(self, symbol, side, size, price, stop_loss, take_profit, signal=None, prob_up=None, explanation=None):
        """Open a new position and log it to trade_log"""
        position = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "entry_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "entry_time": datetime.now(),
            "status": "open",
            "signal": signal,
            "prob_up": prob_up,
            "explanation": explanation
        }
        self.open_positions[symbol] = position

        # Save position to database
        db = get_db()
        db_position = OpenPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=position['entry_time'],
            status='open'
        )
        db.add(db_position)
        db.commit()
        db.close()

        # Add to trade log immediately when position opens
        trade_id = f"{symbol}-{position['entry_time'].timestamp()}"
        trade = {
            "id": trade_id,
            "symbol": symbol,
            "signal": signal,
            "side": side,
            "size": size,
            "entry_price": price,
            "pnl": 0.0,  # Will be updated when position closes
            "entry_time": position['entry_time'],
            "exit_time": None,
            "status": "open",
            "explanation": explanation if explanation else []
        }
        self.trade_log.append(trade)

        # Save trade to database
        db = get_db()
        explanation_str = '|'.join(explanation) if explanation else None
        db_trade = Trade(
            id=trade_id,
            symbol=symbol,
            signal=signal,
            side=side,
            size=size,
            entry_price=price,
            pnl=0.0,
            entry_time=position['entry_time'],
            status='open',
            explanation=explanation_str
        )
        db.add(db_trade)
        db.commit()
        db.close()

        self.log(f"Opened {side} position for {symbol}: {size} @ {price}")

    def close_position(self, symbol, exit_price):
        """Close an existing position and calculate P&L"""
        if symbol not in self.open_positions:
            self.log(f"No open position for {symbol}")
            return

        position = self.open_positions[symbol]
        if position["status"] != "open":
            return

        # Calculate P&L
        if position["side"] == "LONG":
            pnl = (exit_price - position["entry_price"]) * position["size"]
        else:  # SHORT
            pnl = (position["entry_price"] - exit_price) * position["size"]

        # Update equity
        self.state["equity"] += pnl

        # Update the existing trade in trade_log with exit data and P&L
        exit_time = datetime.now()
        for trade in self.trade_log:
            if trade["symbol"] == symbol and trade["status"] == "open":
                trade["exit_price"] = exit_price
                trade["pnl"] = round(pnl, 2)
                trade["exit_time"] = exit_time
                trade["status"] = "closed"
                break

        # Update database
        db = get_db()
        # Update trade in database
        db_trade = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open').first()
        if db_trade:
            db_trade.exit_price = exit_price
            db_trade.pnl = round(pnl, 2)
            db_trade.exit_time = exit_time
            db_trade.status = 'closed'

        # Update position status in database
        db_position = db.query(OpenPosition).filter(OpenPosition.symbol == symbol, OpenPosition.status == 'open').first()
        if db_position:
            db.delete(db_position)  # Delete the closed position from open_positions

        # Update system state
        system_state = db.query(SystemState).filter(SystemState.id == 1).first()
        if system_state:
            system_state.equity = self.state["equity"]
            system_state.last_updated = datetime.now()

        db.commit()
        db.close()

        # Remove position
        position["status"] = "closed"
        del self.open_positions[symbol]

        self.log(f"Closed {position['side']} position for {symbol}: P&L = {pnl:.2f}, New equity = {self.state['equity']:.2f}")

    def check_stop_loss_take_profit(self, symbol, current_price):
        """Check if position should be closed due to stop loss or take profit"""
        if symbol not in self.open_positions:
            return False

        position = self.open_positions[symbol]
        if position["status"] != "open":
            return False

        close_reason = None
        if position["side"] == "LONG":
            if current_price <= position["stop_loss"]:
                close_reason = "stop_loss"
            elif current_price >= position["take_profit"]:
                close_reason = "take_profit"
        else:  # SHORT
            if current_price >= position["stop_loss"]:
                close_reason = "stop_loss"
            elif current_price <= position["take_profit"]:
                close_reason = "take_profit"

        if close_reason:
            self.close_position(symbol, current_price)
            # Update trade reason
            if self.trade_log:
                self.trade_log[-1]["reason"] = close_reason
            return True

        return False

    def create_goal_plan(self, goal):
        self.goal = {
            "target_profit": goal.target_profit,
            "days": goal.days,
            "starting_equity": self.state["equity"]
        }
        daily_target = goal.target_profit / goal.days
        risk_pct = {"conservative":0.003, "moderate":0.007, "aggressive":0.015}[goal.risk_level]
        return {
            "daily_target_usd": round(daily_target,2),
            "risk_pct_per_trade": risk_pct,
            "max_drawdown_pct": goal.max_drawdown_pct,
            "symbols": self.settings["symbols"],
            "notes": "Paper trade first; tighten stops in high vol regimes."
        }

    def start(self):
        self.running = True
        # Save to database
        db = get_db()
        system_state = db.query(SystemState).filter(SystemState.id == 1).first()
        if system_state:
            system_state.running = True
            system_state.last_updated = datetime.now()
        db.commit()
        db.close()
        self.log("Trading bot started")

    def stop(self):
        self.running = False
        # Save to database
        db = get_db()
        system_state = db.query(SystemState).filter(SystemState.id == 1).first()
        if system_state:
            system_state.running = False
            system_state.last_updated = datetime.now()
        db.commit()
        db.close()
        self.log("Trading bot stopped")

    def status(self):
        return {
            "running": self.running, 
            "equity": self.state["equity"],
            "virtual_mode": self.client.virtual_mode if hasattr(self.client, 'virtual_mode') else False,
            "open_positions_count": len(self.open_positions),
            "total_trades": len([t for t in self.trade_log if t.get("pnl", 0) != 0])
        }
    
    
    def step(self, symbol="BTC/USDT"):
        self.log(f"Starting step for symbol: {symbol}")
        raw = self.client.fetch_ohlcv(symbol, timeframe=self.settings["timeframe"], limit=600)
        self.log(f"Fetched {len(raw)} OHLCV data points for {symbol}")
        df = pd.DataFrame(raw, columns=["ts","open","high","low","close","vol"])
        df = regime_features(df)
        self.log(f"Applied regime features to dataframe, shape: {df.shape}")
        if len(df) < 200: 
            self.log("Insufficient data for analysis, skipping step")
            return

        current_price = df.iloc[-1]["close"]
        
        # Check existing positions for stop loss/take profit
        if symbol in self.open_positions:
            closed = self.check_stop_loss_take_profit(symbol, current_price)
            if closed:
                self.log(f"Position closed for {symbol} due to stop loss/take profit")
                # Don't open new position in same step
                return {"action": "position_closed", "symbol": symbol}

        regime = detect_regime(df)
        self.log(f"Detected market regime: {regime}")

        self.log("Fitting model on historical data")
        self.model.fit(df.iloc[:-1])
        prob_up = self.model.predict_proba(df)
        row = df.iloc[-1]
        self.log(f"Model prediction probability for upward move: {prob_up}")

        adaptive = adjust_thresholds(self.state["equity"], self.goal, max(self.goal["days"] - self.elapsed_days, 1))
        self.settings["thresholds"]["long_prob"] = adaptive["long_prob"]
        self.settings["risk_pct"] = adaptive["risk_pct"]
        self.log(f"Adaptive thresholds: long_prob={adaptive['long_prob']}, risk_pct={adaptive['risk_pct']}")

        signal = ensemble_signal(prob_up, row, self.settings["thresholds"])
        self.log(f"Ensemble signal generated: {signal}")
        if signal == "FLAT": 
            self.log("Signal is FLAT, no trade executed")
            return {"action": "no_signal", "symbol": symbol}

        # Only open new position if no existing position
        if symbol in self.open_positions:
            self.log(f"Already have open position for {symbol}, skipping new trade")
            return {"action": "position_exists", "symbol": symbol}

        atr = row["atr"]
        size = position_size(self.state["equity"], self.settings["risk_pct"], atr)
        side = "buy" if signal == "LONG" else "sell"
        self.log(f"Calculated position: size={size}, side={side}, ATR={atr}")

        order = self.client.place_order(symbol, side, size, order_type="market")
        self.log(f"Order placed: {order}")
        s = stops(row["close"], atr, signal)
        self.log(f"Stop loss set at: {s}")

        # Get explanation first
        explanation = explain_trade(signal, prob_up, row, self.settings)
        self.log(f"Trade executed: {signal} {symbol} | Reason: {' | '.join(explanation)}")

        # Open position tracking with all trade data
        position_side = "LONG" if signal == "LONG" else "SHORT"
        stop_loss = s["stop_loss"]
        take_profit = s["take_profit"]
        self.open_position(symbol, position_side, size, current_price, stop_loss, take_profit, signal, prob_up, explanation)

        return {"action": "trade_executed", "order": order, "stops": s, "signal": signal, "prob_up": prob_up, "explanation": explanation}

    def get_performance_summary(self):
        """Get comprehensive performance metrics"""
        if not self.trade_log:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "current_equity": self.state["equity"],
                "open_positions": len(self.open_positions)
            }

        # Count closed trades (those with status="closed")
        closed_trades = [t for t in self.trade_log if t.get("status") == "closed"]
        winning_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in closed_trades if t.get("pnl", 0) < 0]

        total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0.0

        # Calculate profit factor safely
        total_wins = sum(t["pnl"] for t in winning_trades)
        total_losses = abs(sum(t["pnl"] for t in losing_trades))
        if losing_trades and total_losses > 0:
            profit_factor = round(total_wins / total_losses, 2)
        else:
            profit_factor = 0.0 if not winning_trades else 999.99  # Cap at 999.99 for infinite

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(len(winning_trades) / len(closed_trades), 4) if closed_trades else 0.0,
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": profit_factor,
            "current_equity": round(self.state["equity"], 2),
            "open_positions": len(self.open_positions),
            "goal_progress": round((self.state["equity"] - self.goal["starting_equity"]) / self.goal["target_profit"], 4) if self.goal["target_profit"] > 0 else 0.0
        }