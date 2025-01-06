# Content of trading_strategy.py
import numpy as np

class GridBotStrategy:
    def __init__(self, config):
        self.grid_levels = int(config['grid_levels'])
        self.grid_size = float(config['grid_size'])
        self.order_size = int(config['order_size'])
        self.orders = []

    def execute(self, data):
        current_price = data['price']
        self.orders = []
        for i in range(1, self.grid_levels + 1):
            self.orders.append({
                'type': 'buy',
                'price': current_price - (i * self.grid_size),
                'size': self.order_size
            })
            self.orders.append({
                'type': 'sell',
                'price': current_price + (i * self.grid_size),
                'size': self.order_size
            })
        print(f"GridBot orders: {self.orders}")

class TrendFollowingStrategy:
    def __init__(self, config):
        self.ma_period = int(config['moving_average_period'])
        print("From file")
        self.rsi_period = int(config['rsi_period'])
        self.rsi_overbought = int(config['rsi_overbought'])
        self.rsi_oversold = int(config['rsi_oversold'])
        self.prices = []

    def moving_average(self, prices):
        return np.mean(prices[-self.ma_period:])

    def calculate_rsi(self, prices):
        if len(prices) < self.rsi_period + 1:
            return 50  # Neutral RSI when insufficient data
        deltas = np.diff(prices[-(self.rsi_period + 1):])
        gains = deltas[deltas > 0].sum()
        losses = -deltas[deltas < 0].sum()
        if losses == 0:
            return 100
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def detect_trend(self, prices):
        if len(prices) < self.ma_period:
            return "stable"  # Not enough data to determine trend
        ma = self.moving_average(prices)
        recent_price = prices[-1]
        if recent_price > ma * 1.01:  # 1% threshold for growing
            return "growing"
        elif recent_price < ma * 0.99:  # 1% threshold for falling
            return "falling"
        else:
            return "stable"

    def execute(self, data):
        self.prices.append(data['price'])
        if len(self.prices) < self.ma_period:
            return  # Not enough data for moving average
        ma = self.moving_average(self.prices)
        rsi = self.calculate_rsi(self.prices)
        trend = self.detect_trend(self.prices)
        print(f"TrendFollowing - MA: {ma}, RSI: {rsi}, Trend: {trend}")
        if trend == "growing" and rsi < self.rsi_oversold:
            print("Buy Signal")
        elif trend == "falling" and rsi > self.rsi_overbought:
            print("Sell Signal")