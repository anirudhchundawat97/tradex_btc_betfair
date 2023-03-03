from api_caller import ApiCaller
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/lasttradesinfo.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class LastTradesInfo:
    def __init__(self, apitype=None, userid=None):
        print("initialising Last trades info")
        self.api_obj = ApiCaller(apitype, userid)

    def _get_lastTradesInfo_df(self, id):
        resp = self.api_obj.tradex_caller("lastTradesInfo", body={"probeid": id})
        try:
            df = pd.DataFrame(resp["trades"])
            return df
        except:
            logger.warning("Trades key unavailable in api response")
            print("Trades key unavailable in api response")
            return pd.DataFrame()


    def _sort_by_time(self,df):
        df["updatedat"] = pd.to_datetime(df['updatedat'], infer_datetime_format=True)
        df['updatedat'] = df['updatedat'].dt.tz_convert('Asia/Kolkata')
        df = df.sort_values(by="updatedat")
        df.reset_index(inplace=True)
        return df


    def _remap_names(self,df):
        buy_as_a = (df["status"] == "A")
        sell_as_ex = (df["status"] == "EX")
        df["status"] = np.where(buy_as_a, "buy", np.where(sell_as_ex, "sell", None))
        col_rename_map = {'callvalue': 'asset',
                          'coins': 'price',
                          'noofcontracts': 'qty',
                          'status': 'side'}
        df.rename(columns=col_rename_map, inplace=True)
        return df


    def clean_lastTradesInfo_df(self, id):
        df = self._get_lastTradesInfo_df(id)
        if not df.empty:
            df = self._sort_by_time(df)
            df = self._remap_names(df)
            return df
        else:
            logger.warning(f"{id}: No executed trades data.")
            print(f"{id}: No executed trades data.")
            return df



if __name__ == "__main__":
    lti = LastTradesInfo('p', 0)
    print(lti.clean_lastTradesInfo_df(19555))
