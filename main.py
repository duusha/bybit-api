import configparser
from backtester import *
from trading_strategy import *
from bybit_api import batch_data, init_session
import pandas as pd
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import logging
from test_sock import webSoc

def get_data(filename, starting_balance):
    data = pd.read_csv(filename)
    data['Signal'] = None
    data['Trend'] = None
    data['Account Balance'] = starting_balance

def load_config():
    """
    Loads configuration from the 'config.ini' file.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config


def build_graph(config, data, graph_path):
    # Plot the data with signals
    plt.figure(figsize=(12, 6))
    plt.plot(data['startTime'], data['Close'], label='Close Price', color='blue')
    data['MA'] = data['Close'].rolling(window=int(config['trend_following']['moving_average_period'])).mean()
    plt.plot(data['startTime'], data['MA'], label='Moving Average', color='orange')

    # Add buy/sell markers based on the strategy
    # buy_signals = data[data['Signal'] == 'growing']
    buy_signals = data[data['Signal'] == 'falling']
    # sell_signals = data[data['Signal'] == 'falling']
    sell_signals = data[data['Signal'] == 'growing']

    plt.scatter(buy_signals['startTime'], buy_signals['Close'], label='Buy Signal', color='green', marker='^', alpha=1)
    plt.scatter(sell_signals['startTime'], sell_signals['Close'], label='Sell Signal', color='red', marker='v', alpha=1)

    plt.title('Price with Buy/Sell Signals and Account Balance Tracking')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.savefig(graph_path)

def analyze_data(data, trend_strategy, bank_account, symbol, logger):
    for i, row in data.iterrows():
        trend_strategy.execute({'price': row['Close']})
        trend = trend_strategy.detect_trend(data["Close"][:i+1])
        data.at[i, 'Signal'] = trend

        if trend == "falling" and bank_account.cash > 0:
            buy_amount = bank_account.cash * 0.1
            price = row["Close"] ### change to realtime spotdata
            quantity = buy_amount / price
            bank_account.buy(symbol, price, quantity)
            logger.info(f"Buy executed: {quantity} units at {price}")

        elif trend == "growing" and bank_account.assets.get(symbol, 0) > 0:
            sell_quantity = bank_account.assets.get(symbol, 0) * 0.5  # Sell 50% of held quantity
            price = row["Close"] # change to realtime data
            sell_amount = sell_quantity * price
            bank_account.sell(symbol, price, sell_quantity)
            logger.info(f"Sell executed: {sell_quantity} units at {price}")


        # Log balance after each iteration
        data.at[i, 'Account Balance'] = bank_account.cash + (bank_account.assets.get(symbol, 0) * row['Close'])

def create_get_data_path(config):
    paths = {}
    data_path = config["data"]["data_folder"]
    min_1 = os.path.join(data_path, config["data"]["1_min"])
    paths["min_1"] = min_1
    if not os.path.isdir(data_path):
        os.mkdir(data_path)
    if not os.path.isdir(min_1):
        os.mkdir(min_1)
    return paths

def create_get_graph_path(config):
    graph_paths = {}
    data_path = config["data"]["graph_folder"]
    min_1 = os.path.join(data_path, config["data"]["1_min"])
    graph_paths["min_1"] = min_1
    if not os.path.isdir(data_path):
        os.mkdir(data_path)
    if not os.path.isdir(min_1):
        os.mkdir(min_1)
    return graph_paths



### TODO to test on big data
#def concate_by_wind(path):
#    dir_list = os.listdir(path)
#    print(dir_list[0].split("_")[-1].split(".")[0])
#    dir_list.sort(key = lambda x : int(x.split("_")[-1].split(".")[0]))
#    print(dir_list)
#    assert False


def init_logger(config, filename):
    log_path = config["logger"]["log_path"]
    if not os.path.isdir(log_path):
        os.mkdir(log_path)
    logging.basicConfig(filename=os.path.join(log_path, filename),
                    format='%(asctime)s %(message)s',
                    filemode='w')
    logger = logging.getLogger()
    return logger 


def test(config):

    paths =  create_get_data_path(config)
    graph_paths = create_get_graph_path(config)
    starting_balance = float(config["test_account"]["bank_account"] )
    symbol = config["general"]["symbol"]
    session = init_session()
    n_batch = int(config["data"]["number_of_1000s"])
    logger = init_logger(config, "test_1_min.log")
    ### func to collect data
    #batch_data(session, symbol,paths["min_1"], n_batch)
    #func to convert all files to one
    #concate_by_wind(paths["min_1"]) ### TODO to test on big data
    results = pd.DataFrame(columns=["filename", "bankAccount", "heldQuality", "totalIncome"])
    for i in tqdm(range(n_batch), leave=True):
        bank_account = BankAccount(starting_balance) ### update to real bank account data for real data
        trend_strategy = TrendFollowingStrategy(config['trend_following'], bank_account)
        filepath = os.path.join(paths["min_1"], f"1min_{i}.csv")
        df = pd.read_csv(filepath)
        analyze_data(df, trend_strategy, bank_account, symbol, logger)
        build_graph(config, df, os.path.join(graph_paths["min_1"], graph_paths["min_1"].split("/")[-1] + f"_{i}.png"))
        res_row = [filepath, bank_account.cash, bank_account.assets[symbol], (bank_account.get_total_value() - starting_balance) / starting_balance * 100]
        results.loc[len(results)] = res_row
        results.to_csv("results.csv")

def realtime_test(config):
    websock = webSoc(config)
    websock.kline_stream()


if __name__ == "__main__":
    config = load_config()
    if config["general"]["test"]:
        realtime_test(config)
