class BankAccount:
    def __init__(self, initial_balance=1000.0):
        self.cash = initial_balance
        self.assets = {}

    def buy(self, symbol, price, quantity):
        cost = price * quantity
        if self.cash >= cost:
            self.cash -= cost
            self.assets[symbol] = self.assets.get(symbol, 0) + quantity
            return True
        else:
            print("Insufficient cash to buy")
            return False

    def sell(self, symbol, price, quantity):
        if self.assets.get(symbol, 0) >= quantity:
            self.cash += price * quantity
            self.assets[symbol] -= quantity
            if self.assets[symbol] == 0:
                del self.assets[symbol]
            return True
        else:
            print("Insufficient assets to sell")
            return False

    def get_total_value(self, market_prices):
        total_assets_value = sum(market_prices.get(symbol, 0) * quantity for symbol, quantity in self.assets.items())
        return self.cash + total_assets_value

    def export_logs_to_csv(self, file_path):
        import csv
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Cash', 'Assets', 'Total Value'])
            for log in self.logs:
                writer.writerow([
                    log.get('timestamp', 'N/A'),
                    log.get('cash', 0),
                    log.get('assets', {}),
                    log.get('total_value', 0)
                ])
        print(f"Logs exported to {file_path}")

    def __str__(self):
        return f"Cash: ${self.cash:.2f}, Assets: {self.assets}"

class Backtester:
    def __init__(self, live=False, api=None, symbol="BTCUSDT"):
        self.live = live
        self.api = api
        self.symbol = symbol
        self.data = [] if live else self.load_data()
        self.bank_account = BankAccount()
        self.logs = []

    def load_data(self):
        # Load historical data from a file
        return []

    def fetch_live_data(self):
        if self.api:
            return {"price": self.api.get_market_price(self.symbol)}
        return None

    def log_account_state(self, market_price):
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "cash": self.bank_account.cash,
            "assets": self.bank_account.assets.copy(),
            "total_value": self.bank_account.get_total_value({self.symbol: market_price})
        }
        self.logs.append(log_entry)
        print(f"Log Entry: {log_entry}")

    def run(self, strategy):
        if self.live and self.api:
            while True:
                market_data = self.fetch_live_data()
                if market_data:
                    strategy.execute(market_data)
                    self.log_account_state(market_data["price"])
        else:
            for market_data in self.data:
                strategy.execute(market_data)
                self.log_account_state(market_data["price"])
        print("Backtesting complete")

    def print_logs(self):
        print("Account Logs:")
        for log in self.logs:
            print(log)

