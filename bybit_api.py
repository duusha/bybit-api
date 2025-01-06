from pybit.unified_trading import HTTP
import pandas as pd 
import os

session = HTTP(testnet=True)

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

def init_session(symbol="BTCUSD", interval=1, limit=5):
    _ = session.get_kline(
            category = "inverse",
            symbol = symbol,
            interval = interval,
            limit = limit
            )
    return _

def get_new_data(df, data):
    new_list = []
    existing_times = set(df["startTime"].astype(str).unique())
    for row in data:
        print("Time:", row[0], "TimeSeries:", existing_times, "Check: ", (str(row[0]) not in existing_times))
        if str(row[0]) not in existing_times:
            new_list.append(row)
    new_list = new_list[::-1]
    if new_list:
        new_data = pd.DataFrame(new_list, columns=["startTime", "Open", "High", "Low", "Close", "Volume", "Turnover"])
        return new_data, 1
    return None, 0

if __name__ == "__main__":
    filename = "realtime_data.csv"
    df = open_file(filename)
    data_list = init_session()["result"]["list"]

    new_data, is_updated = get_new_data(df, data_list)
    if is_updated:
        df = pd.concat([df, new_data], ignore_index=True)
        new_data.to_csv(filename, mode="a", index=False, header=not os.path.isfile(filename))

    print(df)
