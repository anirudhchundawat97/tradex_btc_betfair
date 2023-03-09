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
        return r


if __name__ == "__main__":
    from pprint import pprint
    from time import sleep(5)
    bf = Betfairfancy()
    # mid = int(input("enter mid: "))
    mid = 32154558
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