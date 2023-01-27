from api_caller import ApiCaller
import pandas as pd
import numpy as np
import logging
import json
from time import sleep

pd.set_option('display.expand_frame_repr', False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
file_handler = logging.FileHandler("log_files/mybets.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class MyBets:

    def __init__(self, apitype=None, userid=None):
        # print("initialising My bets")
        if apitype is None:
            # print("my bets apitype is None")
            self.api_obj = ApiCaller(apitype, userid)
        else:
            self.api_obj = ApiCaller(apitype, userid)

    def _get_portfolio_dict(self):
        resp = self.api_obj.tradex_caller("mybetsv2", {"eventsStatus": "'A','F'"})
        try:
            df = pd.DataFrame(resp["probes"])
            # print(df)
        except:
            logger.warning("probes key unavailable in api response")
            print("probes key unavailable in api response")
        else:
            if not df.empty:
                df = df.set_index("id")[["calls", 'summary']]
                portfolio_dict = df.to_dict("index")
            else:
                portfolio_dict = {}
        return portfolio_dict

    def get_event_holdings(self, id):
        port_dict = self._get_portfolio_dict()
        try:
            event_holdings = port_dict[id]["calls"]
        except KeyError:
            logger.warning(f"{id}: No event holdings")
            print(f"{id}: No event holdings")
            return pd.DataFrame()
        else:
            event_holdings_df = pd.DataFrame(event_holdings)
            col_rename_map = {'callvalue': 'asset',
                              'coins': 'price',
                              'noofcontracts': 'qty',
                              'rank': 'status',
                              'status': 'side',
                              'lastprice': 'buyprice'}
            event_holdings_df.rename(columns=col_rename_map, inplace=True)
            event_holdings_df['status'] = np.where(event_holdings_df['status'] == 0, 'executed', 'pending')
            event_holdings_df['side'] = np.where(event_holdings_df['side'] == 'H', 'sell', 'buy')
            event_holdings_df['buyprice'] = np.where(event_holdings_df['buyprice'] == 0, event_holdings_df['price'], event_holdings_df['buyprice'])
            event_holdings_df['createdat'] = pd.to_datetime(event_holdings_df['createdat'])
            event_holdings_df['createdat'] = event_holdings_df['createdat'].dt.tz_convert('Asia/Kolkata')
            event_holdings_df = event_holdings_df.sort_values(by="createdat", ascending=False)
            event_holdings_df.reset_index(inplace=True)
            return event_holdings_df

    def get_holding_qty(self, id):
        df = self.get_event_holdings(id)
        if not df.empty:
            mask_matched_buy = (df["side"] == "buy") & (df["status"] == "executed")
            mask_unmatched_sell = (df["side"] == "sell")
            true_holdings = df[mask_matched_buy | mask_unmatched_sell]
            mask_asset_yes = true_holdings["asset"] == "Y"
            yes_df = true_holdings[mask_asset_yes]
            if not yes_df.empty:
                yes_qty = yes_df["qty"].sum()
            else:
                yes_qty = 0

            mask_asset_no = true_holdings["asset"] == "N"
            no_df = true_holdings[mask_asset_no]
            if not no_df.empty:
                no_qty = no_df["qty"].sum()
            else:
                no_qty = 0

            return yes_qty, no_qty
        else:
            return 0, 0

    def get_holding_value(self, id):
        df = self.get_event_holdings(id)
        if not df.empty:
            mask_matched_buy = (df["side"] == "buy") & (df["status"] == "executed")
            mask_unmatched_sell = (df["side"] == "sell")
            true_holdings = df[mask_matched_buy | mask_unmatched_sell].copy()
            true_holdings["boughtvalue"] = true_holdings["buyprice"]*true_holdings["qty"]

            mask_asset_yes = true_holdings["asset"] == "Y"
            yes_df = true_holdings[mask_asset_yes]
            if not yes_df.empty:
                yes_value = yes_df.copy()["boughtvalue"].sum()
            else:
                yes_value = 0

            mask_asset_no = true_holdings["asset"] == "N"
            no_df = true_holdings[mask_asset_no]
            if not no_df.empty:
                no_value = no_df.copy()["boughtvalue"].sum()
            else:
                no_value = 0

            return yes_value, no_value
        else:
            return 0, 0

    def get_buy_price(self, id):
        df = self.get_event_holdings(id)
        if not df.empty:
            mask_matched_buy = (df["side"] == "buy") & (df["status"] == "executed")
            mask_unmatched_sell = (df["side"] == "sell")
            true_holdings = df[mask_matched_buy | mask_unmatched_sell]

            mask_asset_yes = true_holdings["asset"] == "Y"
            yes_df = true_holdings[mask_asset_yes]
            if not yes_df.empty:
                yes_buy_price = (yes_df["buyprice"]*yes_df["qty"]).sum() / yes_df["qty"].sum()
            else:
                yes_buy_price = np.nan

            mask_asset_no = true_holdings["asset"] == "N"
            no_df = true_holdings[mask_asset_no]
            if not no_df.empty:
                no_buy_price = (no_df["buyprice"]*no_df["qty"]).sum() / no_df["qty"].sum()
            else:
                no_buy_price = np.nan

            return yes_buy_price, no_buy_price
        else:
            return np.nan, np.nan

    def write_exec_buy_order(self, eid):
        yes_buy, no_buy = self.get_buy_price(eid)
        # yes_buy, no_buy = x,y
        try:
            with open(f"buyprice_json/{eid}.json", "r") as infile:
                prices = json.load(infile)
        except FileNotFoundError:
            prices = {"yesbuy": [],
                      "nobuy": []}
            with open(f"buyprice_json/{eid}.json", "w") as outfile:
                json.dump(prices, outfile)

        if (not np.isnan(yes_buy)) and (yes_buy not in prices["yesbuy"]):
            prices["yesbuy"].append(yes_buy)
        if (not np.isnan(no_buy)) and (no_buy not in prices["nobuy"]):
            prices["nobuy"].append(no_buy)

        with open(f"buyprice_json/{eid}.json", "w") as outfile:
            json.dump(prices, outfile)


if __name__ == "__main__":
    obj = MyBets("p", 0)
    temp1 = obj._get_portfolio_dict()
    ids = temp1.keys()
    print(ids)
    # ids = [13477, 13478, 13479, 13480]
    for id in ids:
        betsdf = pd.DataFrame(temp1[id]["calls"])
        print("BETS ", id)
        print(betsdf)
        # txn_df = get_event_transactions(id)
        # print("TRANSACTIONS ", id)
        # print(txn_df.head())
    # print(temp1.columns)
    # print(get_holding_qty(10618))
    # temp1 = get_event_holdings(10018)
    print(temp1)
    # temp2 = get_buy_price(11929)
    # print(temp2)
    # x = (5,np.nan)
    # print(type(temp2[0]), type(temp2[1]))
    # if np.isnan(temp2[0]):
    #     print("yes")
    # write_exec_buy_order(np.nan,69,6969)
    while True:
        print("waiting")
        sleep(120)
