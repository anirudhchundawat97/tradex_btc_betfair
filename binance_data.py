import binance
import pandas as pd
import datetime as dt

class BinanceApi:
    def __init__(self):
        # self.client = Client()
        self.hist_data = None

    # def get_current_price(self, symbol):
    #     price = self.client.get_avg_price(symbol=symbol)
    #     return price

    def get_current_price(self, symbol):
        alltickerprice_dict = binance.prices()
        ltp = float(alltickerprice_dict[symbol])
        return ltp

    # def fetch_hist_data(self, symbol, interval="1min"):
    #
    #     interval_dict = {"1min": Client.KLINE_INTERVAL_1MINUTE,
    #                      "3min": Client.KLINE_INTERVAL_3MINUTE,
    #                      "5min": Client.KLINE_INTERVAL_5MINUTE,
    #                      "15min": Client.KLINE_INTERVAL_15MINUTE,
    #                      "30min": Client.KLINE_INTERVAL_30MINUTE,
    #                      "1hr": Client.KLINE_INTERVAL_1HOUR,
    #                      "2hr": Client.KLINE_INTERVAL_2HOUR,
    #                      "4hr": Client.KLINE_INTERVAL_4HOUR,
    #                      "6hr": Client.KLINE_INTERVAL_6HOUR,
    #                      "8hr": Client.KLINE_INTERVAL_8HOUR,
    #                      "12hr": Client.KLINE_INTERVAL_12HOUR,
    #                      }
    #     # data = self.client.get_historical_klines(symbol, interval_dict[interval], "1 day ago UTC")
    #     data = self.client.get_historical_klines(symbol, interval_dict[interval], limit=500)
    #     print(interval, len(data))
    #     cols = ["time", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume",
    #             "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"]
    #     df = pd.DataFrame(data, columns=cols)
    #     df = df.astype("float")
    #     df["time"] = pd.to_datetime(df["time"], unit='ms')
    #     df["time"] = df["time"] + dt.timedelta(hours=5, minutes=30)
    #     hist_data = df[["time", "open", "high", "low", "close"]]
    #     return hist_data

    def fetch_hist_data(self, symbol, interval="1min"):
        data = binance.klines(symbol, interval)
        cols = ["time", "open", "high", "low", "close", "volume"]
        df = pd.DataFrame(data, columns=cols)
        df = df.astype("float")
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        df["time"] = df["time"] + dt.timedelta(hours=5, minutes=30)
        hist_data = df[["time", "open", "high", "low", "close"]]
        return hist_data


    def wwma(self, values, n):
        """
         J. Welles Wilder's EMA
        """
        return values.ewm(alpha=1 / n, adjust=False).mean()

    def atr_calc(self, df, n=14):
        data = df.copy()
        high = data["high"]
        low = data["low"]
        close = data["close"]
        data['tr0'] = abs(high - low)
        data['tr1'] = abs(high - close.shift(1))
        data['tr2'] = abs(low - close.shift(1))
        tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
        atr = self.wwma(tr, n)
        return atr

    def ma_calc(self, df, n):
        data = df.copy()
        data[f"ma_{n}"] = data["close"].rolling(n).mean()
        return data[f"ma_{n}"]

    def ma_custom_indi(self, df, n_s, n_l, threshold=0.5):
        data = df.copy()
        data["ma_s"] = self.ma_calc(data, n_s)
        data["ma_l"] = self.ma_calc(data, n_l)
        data["ma_sl_diff"] = (data["ma_l"] - data["ma_s"]).abs()
        last_ma_s = data["ma_s"].iloc[-1]
        last_ma_l = data["ma_l"].iloc[-1]
        avg_ma_sl_diff = data["ma_sl_diff"].mean()
        last_ma_sl_diff = data["ma_sl_diff"].iloc[-1]
        threshold_ma_sl_diff = avg_ma_sl_diff * threshold
        if last_ma_sl_diff < threshold_ma_sl_diff:
            return 0
        elif (last_ma_sl_diff > threshold_ma_sl_diff) and (last_ma_s > last_ma_l):
            return 1
        elif (last_ma_sl_diff > threshold_ma_sl_diff) and (last_ma_s < last_ma_l):
            return -1
        else:
            print("last_ma_s: ", last_ma_s)
            print("last_ma_l: ", last_ma_l)
            print("avg_ma_sl_diff: ", avg_ma_sl_diff)
            print("last_ma_sl_diff: ", last_ma_sl_diff)
            print("threshold_ma_sl_diff: ", threshold_ma_sl_diff)
            return 0
    def get_last_atr(self, symbol, interval):
        data = self.fetch_hist_data(symbol, interval)
        atr1 = self.atr_calc(data, n=14)
        return atr1.iloc[-1]

    def get_cutom_indi_value(self, symbol, interval):
        data = self.fetch_hist_data(symbol, interval)
        return self.ma_custom_indi(data, 14, 28)




if __name__=="__main__":
    cl = BinanceApi()
    coins = ["BTCUSDT", "ETHUSDT", "SHIBUSDT", "DOGEUSDT", "GBPUSDT", "EURUSDT"]
    for c in coins:
        x = cl.get_last_atr(c, "5min")
        print(c, " : ", x)
        print(cl.fetch_hist_data(c, "1hr"))
    # exit()
    x = cl.get_last_atr("BTCUSDT", "1min")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "3min")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "5min")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "15min")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "30min")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "1hr")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "2hr")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "4hr")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "6hr")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "8hr")
    print(x)
    x = cl.get_last_atr("BTCUSDT", "12hr")
    print(x)

    # time = dt.datetime(2022,10,31,18,0,0)
    # now = dt.datetime.now()
    # if time-now <= dt.timedelta(hours=7):
    #     print(time-now, "yesss")
    # elif time-now > dt.timedelta(minutes=60):
    #     print(time-now, "Noooo")
    # else:
    #     print(time-now, "mehhh")
