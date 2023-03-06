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
        url = f"https://betfairoddsapi.com:3444/api/bm_fancy/{mid}"
        r = requests.get(url)
        return r


if __name__ == "__main__":
    bf = Betfairfancy()
    r = bf.make_api_call(1.210819651)
    print(r.text)
    print(json.loads(r.text))