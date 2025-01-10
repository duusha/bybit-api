import configparser
from backtester import Backtester
from trading_strategy import *
def load_config():
    """
    Loads configuration from the 'config.ini' file.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config


def main():

    config = load_config()
    bybit_config = config['bybit']
#    api = BybitAPI(bybit_config['api_key'], bybit_config['api_secret'])

    # Initialize the backtester with live trading enabled
    backtester = Backtester(live=True)

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

if __name__ == '__main__':
    main()

