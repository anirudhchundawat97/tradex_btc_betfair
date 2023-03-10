import requests
import pandas as pd
import datetime as dt
import json

class PolygonApi:
    def __init__(self):
        self.hist_data = None
        self.apikey = "70e5hjHXdKSMCM4PGjqmsrwHQrvP3lVK"

    def get_current_price(self, symbol):
        url = f"https://api.polygon.io/v2/last/nbbo/{symbol}?apiKey={self.apikey}"
        r = requests.get(url)
        price = json.loads(r.text)["results"]["P"]
        return price

    def fetch_hist_data(self, symbol, interval="1min"):
        date_now = (dt.datetime.now() - dt.timedelta(hours=5, minutes=30)).date().strftime("%Y-%m-%d")
        date_yest = (dt.datetime.now() - dt.timedelta(days =1, hours=5, minutes=30)).date().strftime("%Y-%m-%d")

        interval_dict = {"1min": {"interval_multiplier": 1, "interval": "minute"},
                         "3min": {"interval_multiplier": 3, "interval": "minute"},
                         "5min": {"interval_multiplier": 5, "interval": "minute"},
                         "15min": {"interval_multiplier": 15, "interval": "minute"},
                         "30min": {"interval_multiplier": 30, "interval": "minute"},
                         "1hr": {"interval_multiplier": 1, "interval": "hour"},
                         "2hr": {"interval_multiplier": 2, "interval": "hour"},
                         "4hr": {"interval_multiplier": 4, "interval": "hour"},
                         "6hr": {"interval_multiplier": 6, "interval": "hour"},
                         "8hr": {"interval_multiplier": 8, "interval": "hour"},
                         "12hr": {"interval_multiplier": 12, "interval": "hour"},
                         }
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/" \
              f"{interval_dict[interval]['interval_multiplier']}/" \
              f"{interval_dict[interval]['interval']}/" \
              f"{date_yest}/" \
              f"{date_now}?adjusted=true&sort=asc&" \
              f"limit=999999999&apiKey={self.apikey}"
        # print(url)
        r = requests.get(url)
        data = pd.DataFrame(json.loads(r.text)["results"])
        data = data[["o","c","h","l","t"]]
        print(interval, len(data))
        cols = ["open", "close", "high", "low", "time"]
        data.columns = cols
        data["time"] = pd.to_datetime(data["time"], unit='ms')
        data["time"] = data["time"] + dt.timedelta(hours=5, minutes=30)
        hist_data = data[["time", "open", "high", "low", "close"]]
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
    cl = PolygonApi()
    coins = ["NFLX", "ETHUSDT", "SHIBUSDT", "DOGEUSDT", "GBPUSDT", "EURUSDT"]
    for c in coins:
        x = cl.get_last_atr(c, "5min")
        print(c, " : ", x)
        print(cl.fetch_hist_data(c, "1hr"))
    exit()
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
