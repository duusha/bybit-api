from pybit.unified_trading import HTTP
import pandas as pd 
import os
from tqdm import tqdm


#print(session.get_kline(
#    category="inverse",
#    symbol="BTCUSD",
#    interval=1,
#))


### create logs

def open_file(filename):
    if not os.path.isfile(filename):
        df = pd.DataFrame(columns=["startTime", "Open", "High", "Low", "Close", "Volume", "Turnover"])
    else:
        df = pd.read_csv(filename)
    return df

def init_session():
    session = HTTP(testnet=True)
    return session

def init_kline(session, symbol="BTCUSD", interval=1, limit=2000):
    _ = session.get_kline(
            category = "linear",
            symbol = symbol,
            interval = interval,
            limit = limit
            )
    return _

def get_new_data(df, data, filename):
    new_list = []
    existing_times = set(df["startTime"].astype(str).unique())
    for row in data:
        if str(row[0]) not in existing_times:
            new_list.append(row)
    new_list = new_list[::-1]
    if new_list:
        new_data = pd.DataFrame(new_list, columns=["startTime", "Open", "High", "Low", "Close", "Volume", "Turnover"])
        df = pd.concat([df, new_data], ignore_index=True) ### added
    df.to_csv(filename, mode="w", index=False, header = not os.path.isfile(filename))
        #return new_data, 1
    #return None, 0

def batch_data(session, symbol, path_to_data, num = 1000):
    serverTime = session.get_server_time()
    print(serverTime)
    serverTimeSec = int(serverTime["time"]) ### time of getting response
    for i in tqdm(range(num)):
        batch_name = path_to_data.split("/")[-1] + f"_{i}.csv"
        path_to_batch = os.path.join(path_to_data, batch_name)
        print(path_to_batch)
        startTime = serverTimeSec - (i + 1) * num * 1000 * 60
        kline = session.get_kline(
            category = "inverse",
            symbol = symbol,
            interval = 1,
            limit = 1000,
            start = startTime,
            )
        data_list = kline["result"]["list"]
        data_list = data_list[::-1] ### reverse to increse order 
        df = pd.DataFrame(data_list, columns=["startTime", "Open", "High", "Low", "Close", "Volume", "Turnover"])
        df.to_csv(path_to_batch, mode="w", index=False)
        


if __name__ == "__main__":
    filename = "realtime_data_1min.csv"
    df = open_file(filename)
    session = init_session()
    data_list = session["result"]["list"]
    get_new_data(df, data_list, filename)
    batch_data(session)
#    new_data, is_updated = get_new_data(df, data_list)
#    if is_updated:
#        df = pd.concat([df, new_data], ignore_index=True)
#        new_data.to_csv(filename, mode="a", index=False, header=not os.path.isfile(filename))

    print(df)
