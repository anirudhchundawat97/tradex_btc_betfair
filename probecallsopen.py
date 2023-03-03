from api_caller import ApiCaller
import pandas as pd
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/probecallsopen.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def _remap_columns(df):
    df["value"] = df["coins"]*df["noofcontracts"]
    col_rename_map = {'callvalue': 'asset',
                      'coins': 'price',
                      'noofcontracts': 'qty'}
    df.rename(columns=col_rename_map, inplace=True)
    _cols = ["asset", "price", "qty", "value"]
    return df[_cols]


class ProbeCallsOpen:
    def __init__(self, apitype=None, userid=None):
        print("initialising Probe Calls open")
        self.api_obj = ApiCaller(apitype, userid)

    def _get_orderbook(self, id):
        try:
            resp = self.api_obj.tradex_caller("probecalls/open", {"probeid": id})
            df = pd.DataFrame(resp["calls"])
            return df
        except:
            logger.warning("calls key unavailable in api response")
            print("calls key unavailable in api response")
            return pd.DataFrame()

    def get_yesno_orderbook(self, id):
        df = self._get_orderbook(id)
        if not df.empty:
            df = _remap_columns(df)
            df_y = df[df["asset"] == "Y"]
            df_y = df_y.sort_values(by="price", ascending=False).reset_index()
            df_n = df[df["asset"] == "N"]
            df_n = df_n.sort_values(by="price", ascending=False).reset_index()
            return df, df_y, df_n
        else:
            logger.warning(f"{id}: No Order Book data.")
            print(f"{id}: No Order Book data.")
            return df, df, df

if __name__ == "__main__":
    id = 17032
    # resp = tradex_caller("probecalls/open", {"probeid": id})
    # print(resp)
    # print(get_yesno_orderbook(id))
    pco = ProbeCallsOpen('p', 0)
    df = pco._get_orderbook(id)
    print(df)
    # df2 = pco.