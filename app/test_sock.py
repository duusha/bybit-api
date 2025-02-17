import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from time import sleep
from backtester import BankAccount
from trading_strategy import TrendFollowingStrategy

import logging
import os

# Создаем папку logs, если её нет
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "app.log")),
        logging.StreamHandler()
    ]
)

class WebSoc:
    def __init__(self, config):
        self.config = config
        self.df = pd.DataFrame(columns=["start", "end", "open", "close", "high", "low", "volume"])
        self.bank_account = BankAccount(1000)  # Starting balance
        self.orders = []  # Track active orders
        self.graph_path = "graphs/orders_1min"
        os.makedirs(self.graph_path, exist_ok=True)
        self.strategy = TrendFollowingStrategy(config["trend_following"], self.bank_account)
        self.local_test = config.get("local_test", False)  # New local test flag

    def handle_message(self, message):
        """Handles incoming WebSocket messages, processes only confirmed candles."""
        try:
            if "data" not in message or len(message["data"]) == 0:
                logging.error("Malformed WebSocket message: Missing 'data' field")
                return

            kline_data = message["data"][0]
            required_fields = ["start", "end", "open", "close", "high", "low", "volume", "confirm"]
            if not all(field in kline_data for field in required_fields):
                logging.error(f"Malformed WebSocket message: {kline_data}")
                return

            new_data = {
                "start": kline_data["start"],
                "end": kline_data["end"],
                "open": float(kline_data["open"]),
                "close": float(kline_data["close"]),
                "high": float(kline_data["high"]),
                "low": float(kline_data["low"]),
                "volume": float(kline_data["volume"]),
            }
            self.df.loc[len(self.df)] = new_data

            market_data = {"price": new_data["close"]}
            if kline_data["confirm"]:
                order_filled = self.check_orders(market_data)
                if order_filled:
                    self.plot_graph()
                order = self.place_orders(market_data)
                if order:
                    self.plot_graph()

        except Exception as e:
            logging.error(f"Error handling message: {e}")
            assert False

    def place_orders(self, market_data):
        """Executes strategy and places new buy/sell orders."""
        order = self.strategy.execute(market_data)
        if order and not any(o['price'] == order['price'] and o['type'] == order['type'] for o in self.orders):
            self.orders.append(order)
            logging.info(f"Order Placed: {order['type']} at {order['price']}")
            return order
        return None

    def check_orders(self, market_data):
        """Checks if existing open orders should be executed."""
        current_price = market_data["price"]
        for order in self.orders:
            if order["status"] == "open":
                if order["type"] == "buy" and current_price <= order["price"]:
                    self.bank_account.buy("BTCUSDT", order["price"], order["quantity"])
                    order["status"] = "filled"
                    logging.info(f"Buy Order Filled at {order['price']}")
                    return True
                elif order["type"] == "sell" and current_price >= order["price"]:
                    self.bank_account.sell("BTCUSDT", order["price"], order["quantity"])
                    order["status"] = "filled"
                    logging.info(f"Sell Order Filled at {order['price']}")
                    return True
        return False

    def plot_graph(self):
        """Plots order placements and executions."""
        plt.figure(figsize=(12, 6))
        plt.plot(self.df["start"], self.df["close"], label="Close Price", color="blue")

        for order in self.orders:
            color = "green" if order["type"] == "buy" else "red"
            plt.scatter(order["price"], order["price"], color=color, marker="o", label=f"{order['type'].capitalize()} at {order['price']}")

        plt.title("Order Placement and Execution")
        plt.xlabel("Timestamp")
        plt.ylabel("Price")
        plt.legend()
        plt.grid()
        graph_filename = os.path.join(self.graph_path, "order_tracking.png")
        plt.savefig(graph_filename)
        plt.close()

    def simulate_test_data(self):
        """Simulate market data for local testing focused on order execution."""
        logging.info("Running in local test mode...")

        # Simulated price trend: Starts at 100 and gradually increases/decreases
        base_price = 100
        test_data = []

        for i in range(30):
            # Alternate between rising and falling patterns every 10 candles
            if i < 10:
                # Simulate a downtrend to create oversold conditions (for buy signals)
                close_price = base_price - i
            elif i < 20:
                # Simulate an uptrend to create overbought conditions (for sell signals)
                close_price = base_price - 10 + (i - 10) * 2
            else:
                # Sideways market to test stable signals
                close_price = 100 + (i % 2) * 2

            open_price = close_price - 1
            high_price = close_price + 2
            low_price = close_price - 2
            volume = 1000 + i * 100

            test_data.append({
                "start": i * 60,
                "end": (i + 1) * 60,
                "open": round(open_price, 2),
                "close": round(close_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": volume,
                "confirm": True
            })

            base_price = close_price

        # Feed test data into the system
        for msg in test_data:
            logging.info(f"TEST DATA: Processing candle with close price: {msg['close']}")
            self.handle_message({"data": [msg]})
            sleep(0.5)

        logging.info(f"Final Bank Account: {self.bank_account}")
        logging.info(f"Final Open Orders: {self.orders}")

    def start_stream(self):
        """Starts the WebSocket stream or local test."""
        if self.local_test:
            self.simulate_test_data()
            return

        while True:
            try:
                from pybit.unified_trading import WebSocket
                logging.info("Connecting to WebSocket...")
                self.ws = WebSocket(testnet=False, channel_type="linear")
                self.ws.kline_stream(interval=1, symbol="BTCUSDT", callback=self.handle_message)
                logging.info("WebSocket connection established.")
                while True:
                    sleep(1)  # Keep the main thread alive
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                logging.info("Restarting WebSocket connection...")
                sleep(5)


if __name__ == "__main__":
    config = {
        "trend_following": {
            "moving_average_period": 14,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        },
        "local_test": False  # Set this to False for live mode
    }

    ws = WebSoc(config)
    ws.start_stream()

