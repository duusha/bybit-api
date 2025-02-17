import logging 
import pandas as pd
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
            self.orders.append({"type": "buy", "price": buy_price, "quantity": self.order_size, "status": "open"})
            self.orders.append({"type": "sell", "price": sell_price, "quantity": self.order_size, "status": "open"})

        print(f"GridBot placed orders at Buy: {buy_price}, Sell: {sell_price}")
        return self.orders


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
            return "stable"

        moving_average = self.calculate_moving_average()
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

        return "stable"

    def execute(self, market_data):
        current_price = market_data["price"]
        if len(self.prices) > 0 and self.prices[-1] == current_price:
            logging.info(f"Duplicate price detected: {current_price}. Skipping...")
            return None  # Don't add the same price again

        self.prices.append(current_price)

        # Calculate Indicators
        moving_average = self.calculate_moving_average()
        rsi = self.calculate_rsi()
        logging.info(f"MA:{moving_average} RSI: {rsi} Prices: {self.prices}")

        # Ensure enough data is available
        if moving_average is None or rsi is None:
            return None  

        # Order sizing rules
        buy_allocation = 0.1  # 10% of available cash
        sell_allocation = 0.5  # 50% of held assets
        min_buy_amount = 50  # Minimum buy amount in USD

        # **Buy Condition**
        if rsi < self.rsi_oversold and current_price > moving_average and self.bank_account.cash > 0:
            buy_amount = self.bank_account.cash * buy_allocation
            if buy_amount < min_buy_amount:
                return None  # Skip small trades

            quantity = buy_amount / current_price
            self.bank_account.buy("BTCUSDT", current_price, quantity)
            return {"type": "buy", "price": current_price, "quantity": quantity}

        # **Sell Condition**
        elif rsi > self.rsi_overbought and current_price < moving_average and self.bank_account.assets.get("BTCUSDT", 0) > 0:
            sell_quantity = self.bank_account.assets.get("BTCUSDT", 0) * sell_allocation
            self.bank_account.sell("BTCUSDT", current_price, sell_quantity)
            return {"type": "sell", "price": current_price, "quantity": sell_quantity}

        return None  # No trade executed

    def calculate_rsi(self):
        """Calculates the RSI (Relative Strength Index) using the correct rolling mean approach."""
        if len(self.prices) < self.rsi_period + 1:
            return None  # Not enough data to calculate RSI

        # Convert prices to a Pandas Series
        prices_series = pd.Series(self.prices)
        deltas = prices_series.diff()  # Price changes

        # Calculate gains (positive deltas) and losses (negative deltas)
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        # Use exponential moving average (EMA) for smoothing (better than simple mean)
        avg_gain = gains.ewm(span=self.rsi_period, adjust=False).mean()
        avg_loss = losses.ewm(span=self.rsi_period, adjust=False).mean()

        # Compute the Relative Strength (RS) and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

    def calculate_moving_average(self):
        """Calculates the moving average over the defined period."""
        if len(self.prices) < self.moving_average_period:
            return None
        return sum(self.prices[-self.moving_average_period:]) / self.moving_average_period

