from binance import Client
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
client = Client()

# fetch 1 minute klines for the last day up until now
klines = client.\
    get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 day ago UTC")

# # fetch 30 minute klines for the last month of 2017
# klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
#
# # fetch weekly klines since it listed
# klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
avg_price = client.get_avg_price(symbol='BTCUSDT')

cols = ["time","open","high","low","close","volume","close_time","quote_asset_volume", "number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"]
frame = pd.DataFrame(klines, columns=cols)
frame =frame.astype("float")
# frame["time"] = frame["time"] / 1000
frame["time"] = pd.to_datetime(frame["time"], unit='ms')
frame["time"] = frame["time"] + dt.timedelta(hours=5, minutes=30)
# print(frame)jj
print(avg_price)
print(frame.columns)
hist_data = frame[["time","open","high","low","close"]]
print(hist_data)

print(hist_data.info())

def wwma(values, n):
    """
     J. Welles Wilder's EMA
    """
    return values.ewm(alpha=1/n, adjust=False).mean()

def atr(df, n=14):
    data = df.copy()
    high = data["high"]
    low = data["low"]
    close = data["close"]
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift(1))
    data['tr2'] = abs(low - close.shift(1))
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(tr, n)
    return atr

hist_data["atr1"] = atr(hist_data,14)
hist_data["atr+"] = hist_data["atr1"] + hist_data["close"]
hist_data["atr-"] = hist_data["close"] - hist_data["atr1"]
print(hist_data)
hist_data[["close","atr+","atr-"]].plot()
plt.show()