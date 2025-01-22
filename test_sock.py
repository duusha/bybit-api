from pybit.unified_trading import WebSocket
from time import sleep
import pandas as pd 

class webSoc():
    def __init__(self, config):
        self.ws = WebSocket(
            testnet=False,
            channel_type="linear",
        )
        self.df = pd.DataFrame(columns=["start", "end", "open", "close", "high", "low", "volume"])
# message example
#        {'topic': 'kline.5.BTCUSDT', 'data': [{'start': 1737567600000, 'end': 1737567899999, 'interval': '5', 'open': '104524.1', 'close': '104360', 'high': '104593.5', 'low': '104360', 'volume': '124.161', 'turnover': '12977377.672', 'confirm': False, 'timestamp': 1737567730559}], 'ts': 1737567730559, 'type': 'snapshot'}

    def handle_message(self, message):
        if message["data"][0]["confirm"]:
            self.df.loc[len(self.df)] = [
                    message["data"][0]["start"],
                    message["data"][0]["end"],
                    message["data"][0]["open"],
                    message["data"][0]["close"],
                    message["data"][0]["high"],
                    message["data"][0]["low"],
                    message["data"][0]["volume"],
                    ]
            print(self.df)
    def kline_stream(self,):
        self.ws.kline_stream(
            interval=1,
            symbol="BTCUSDT",
            callback=self.handle_message
        )
if __name__ == "__main__":
    _ = webSoc()
    _.kline_stream()
    while 1:
        continue
