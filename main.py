import configparser
from backtester import Backtester
from trading_strategy import GridBotStrategy, TrendFollowingStrategy
from bybit_api import BybitAPI  # Ensure you have BybitAPI or remove if not used


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def main():
    config = load_config()
    bybit_config = config['bybit']
    api = BybitAPI(bybit_config['api_key'], bybit_config['api_secret'])

    # Initialize the backtester with live trading enabled
    backtester = Backtester(live=True, api=api, symbol="BTCUSDT")

    # Initialize the bank account
    bank_account = backtester.bank_account

    # Decide which strategy to use
    if config['DEFAULT'].getboolean('use_grid_bot', fallback=True):
        strategy = GridBotStrategy(config['grid_bot'], bank_account)
    else:
        strategy = TrendFollowingStrategy(config['trend_following'], bank_account)
    
    # Run backtesting or live trading
    backtester.run(strategy)
    backtester.print_logs()
    # Export logs to a CSV file
    backtester.bank_account.export_logs_to_csv('backtester_logs.csv')

if __name__ == '__main__':
    main()
