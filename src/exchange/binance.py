import ccxt
from datetime import datetime

class BinanceClient:
    def __init__(self, key, secret, testnet=True):
        self.virtual_mode = key == "your-binance-api-key" or secret == "your-binance-api-secret"
        self.virtual_trades = []
        
        if self.virtual_mode:
            print("🔄 Running in VIRTUAL TRADING MODE - No real trades will be executed")
            self.exchange = None
        else:
            self.exchange = ccxt.binance({
                "apiKey": key,
                "secret": secret,
                "enableRateLimit": True,
            })
            if testnet:
                self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="5m", limit=500):
        if self.virtual_mode:
            # In virtual mode, we still need real market data for analysis
            # Use KuCoin instead of Binance to avoid geo-restrictions
            temp_exchange = ccxt.kucoin({"enableRateLimit": True})
            return temp_exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def place_order(self, symbol, side, amount, order_type="market"):
        if self.virtual_mode:
            # Simulate successful order placement
            order_id = f"virtual_{datetime.now().timestamp()}"
            simulated_order = {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "type": order_type,
                "status": "filled",
                "timestamp": datetime.now().timestamp() * 1000,
                "virtual": True
            }
            self.virtual_trades.append(simulated_order)
            print(f"📊 VIRTUAL ORDER: {side.upper()} {amount} {symbol} - Order ID: {order_id}")
            return simulated_order
        
        return self.exchange.create_order(symbol, order_type, side, amount)

    def get_balance(self):
        if self.virtual_mode:
            # Return simulated balance
            return {
                "total": {"USDT": 1000.0},
                "free": {"USDT": 1000.0},
                "used": {"USDT": 0.0},
                "virtual": True
            }
        return self.exchange.fetch_balance()

    def get_virtual_trades(self):
        """Get all virtual trades executed"""
        return self.virtual_trades