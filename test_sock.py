from pybit.unified_trading import WebSocket
from time import sleep
import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from backtester import BankAccount
from trading_strategy import TrendFollowingStrategy

logging.basicConfig(level=logging.INFO)

class WebSoc:
    def __init__(self, config):
        self.config = config
        self.df = pd.DataFrame(columns=["start", "end", "open", "close", "high", "low", "volume"])
        self.bank_account = BankAccount(1000)  # Starting balance
        self.orders = []  # Track active orders
        self.graph_path = "graphs/orders_1min"
        os.makedirs(self.graph_path, exist_ok=True)
        self.strategy = TrendFollowingStrategy(config["trend_following"], self.bank_account)

    def handle_message(self, message):
        """Handles incoming WebSocket messages, processes only confirmed candles."""
        try:
            if "data" not in message or len(message["data"]) == 0:
                logging.error("Malformed WebSocket message: Missing 'data' field")
                return

            kline_data = message["data"][0]

            # Ensure necessary fields exist
            required_fields = ["start", "end", "open", "close", "high", "low", "volume", "confirm"]
            if not all(field in kline_data for field in required_fields):
                logging.error(f"Malformed WebSocket message: {kline_data}")
                return


            # Process confirmed data
            new_data = {
                "start": kline_data["start"],
                "end": kline_data["end"],
                "open": float(kline_data["open"]),
                "close": float(kline_data["close"]),
                "high": float(kline_data["high"]),
                "low": float(kline_data["low"]),
                "volume": float(kline_data["volume"]),
            }

            self.df.loc[len(self.df)] = new_data  # Append only confirmed data

            # Pass only the 'close' price as market data
            market_data = {"price": new_data["close"]}
            if kline_data["confirm"]:
                # Check if any existing orders should be executed
                order_filled = self.check_orders(market_data)
                if order_filled:
                    self.plot_graph()

                # Execute strategy and place new orders
                order = self.place_orders(market_data)


                if order:
                    self.plot_graph()

        except Exception as e:
            logging.error(f"Error handling message: {e}")

    def place_orders(self, market_data):
        """Executes strategy and places new buy/sell orders."""
        order = self.strategy.execute(market_data)
        if order:
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

    def start_stream(self):
        """Starts the WebSocket stream and manages reconnections."""
        while True:
            try:
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
    config = {"trend_following": {"moving_average_period": 14, "rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30}}
    ws = WebSoc(config)
    ws.start_stream()

