import json
import pandas as pd
# import gspread as gs
# import datetime as dt
# from zoneinfo import ZoneInfo
# import bf_sheet_config as config
import requests

# #get yyyy-mm format for API call
# now = dt.datetime.now(tz=ZoneInfo('Asia/Kolkata'))
# today = now.date()
# tomorrow = today + dt.timedelta(days=1)

class Betfairfancy:
    def __init__(self):
        self.mid = None

    def make_api_call(self, mid):
        url = f"https://betfairoddsapi.com:3444/api/bm_fancy/{str(mid)}"
        r = requests.get(url)
        r_json = json.loads(r.text)
        # pprint(r_json)
        # print(r_json.keys())
        r_data = r_json["data"]
        # pprint(r_data)
        r_t3 = r_data["t3"]
        t3_df = pd.DataFrame(r_t3)
        t3_df["nat"] = t3_df["nat"].astype(str).replace(" ", "").lower()
        return t3_df

    def get_backlay_odds(self, description):
        split = description.split("|")
        mid = int(split[3])
        nat = split[2].replace(" ", "").lower()
        r = self.make_api_call(mid)
        filtered_df = r[r["nat"] == nat]
        bs1 = filtered_df["bs1"]
        ls1 = filtered_df["ls1"]
        win_probability = 10000 / (bs1+100)
        loss_probability = 100 - win_probability
        return win_probability, loss_probability


if __name__ == "__main__":
    from pprint import pprint
    from time import sleep
    bf = Betfairfancy()
    # mid = int(input("enter mid: "))
    mid = 32158858
    while True:
        r = bf.make_api_call(mid)
        # print(r.text)
        r_json = json.loads(r.text)
        pprint(r_json)
        # print(r_json.keys())
        r_data = r_json["data"]
        pprint(r_data)
        r_t3 = r_data["t3"]
        t3_df = pd.DataFrame(r_t3)
        print(t3_df)
        sleep(5)