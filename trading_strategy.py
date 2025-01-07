class GridBotStrategy:
    def __init__(self, config, bank_account):
        self.grid_levels = int(config['grid_levels'])
        self.grid_size = float(config['grid_size'])
        self.order_size = int(config['order_size'])
        self.bank_account = bank_account
        self.orders = []

    def execute(self, data):
        current_price = data['price']
        for i in range(1, self.grid_levels + 1):
            buy_price = current_price - (i * self.grid_size)
            sell_price = current_price + (i * self.grid_size)
            self.bank_account.buy("BTCUSDT", buy_price, self.order_size)
            self.bank_account.sell("BTCUSDT", sell_price, self.order_size)
        print(f"GridBot executed trades. Account: {self.bank_account}")
        # Log executed trades
        print(f"Executed Trades: Bought at {buy_price}, Sold at {sell_price}")

class TrendFollowingStrategy:
    def __init__(self, config, bank_account):
        self.moving_average_period = int(config['moving_average_period'])
        self.rsi_period = int(config['rsi_period'])
        self.rsi_overbought = int(config['rsi_overbought'])
        self.rsi_oversold = int(config['rsi_oversold'])
        self.bank_account = bank_account
        self.prices = []

    def detect_trend(self, prices):
        """
        Detects the trend based on moving average, RSI, and price movement.
        Args:
            prices: A Pandas Series or list of prices to calculate trend from.
        Returns:
            'growing', 'falling', or 'stable'
        """
        if len(prices) < self.moving_average_period:
            return "stable"  # Not enough data to determine trend
        
        moving_average = prices[-self.moving_average_period:].mean()
        current_price = prices.iloc[-1]
        previous_price = prices.iloc[-2] if len(prices) > 1 else current_price
    
        # RSI Calculation
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0).rolling(window=self.rsi_period).mean()
        losses = -deltas.where(deltas < 0, 0).rolling(window=self.rsi_period).mean()
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs.iloc[-1])) if not rs.iloc[-1] is None else None
    
        if moving_average is None or rsi is None:
            return "stable"
    
        # Trend decision based on RSI
        if rsi < self.rsi_oversold:
            return "falling"  # Oversold conditions
        elif rsi > self.rsi_overbought:
            return "growing"  # Overbought conditions
    
        # Additional check for price movement relative to moving average
        if current_price > moving_average and previous_price <= moving_average:
            return "growing"
        elif current_price < moving_average and previous_price >= moving_average:
            return "falling"
    
        # Default case
        return "stable"
        
    def calculate_moving_average(self):
        if len(self.prices) < self.moving_average_period:
            return None
        return sum(self.prices[-self.moving_average_period:]) / self.moving_average_period

    def calculate_rsi(self):
        if len(self.prices) < self.rsi_period + 1:
            return None
        gains = 0
        losses = 0
        for i in range(-self.rsi_period, 0):
            change = self.prices[i] - self.prices[i - 1]
            if change > 0:
                gains += change
            else:
                losses -= change
        if losses == 0:
            return 100
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def execute(self, data):
        current_price = data['price']
        self.prices.append(current_price)

        moving_average = self.calculate_moving_average()
        rsi = self.calculate_rsi()

        if moving_average is None or rsi is None:
            return

        if current_price > moving_average and rsi < self.rsi_oversold:
           # self.bank_account.buy("BTCUSDT", current_price, 1)
           # print(f"TrendFollowing: Bought at {current_price}")
            self.bank_account.sell("BTCUSDT", current_price, 1)
            print(f"TrendFollowing: Sold at {current_price}")
        elif current_price < moving_average and rsi > self.rsi_overbought:
           # self.bank_account.sell("BTCUSDT", current_price, 1)
           # print(f"TrendFollowing: Sold at {current_price}")
            self.bank_account.buy("BTCUSDT", current_price, 1)
            print(f"TrendFollowing: Bought at {current_price}")

