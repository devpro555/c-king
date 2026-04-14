from strategy.executor import TradingExecutor
from utils.config import load_settings
import time

settings = load_settings()
executor = TradingExecutor(settings)

executor.start()
while executor.running:
    for symbol in settings["symbols"]:
        result = executor.step(symbol)
        if result:
            print(result)
    time.sleep(300)  # 5 minutes