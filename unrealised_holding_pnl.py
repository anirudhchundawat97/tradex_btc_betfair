from api_caller import ApiCaller
import pandas as pd
import numpy as np
import datetime as dt

pd.set_option("display.max_columns", 500)
pd.set_option('display.expand_frame_repr', False)

class HoldingPnl:
    def __init__(self, event_id,apitype=None, userid=None):
        self.api_obj = ApiCaller(apitype, userid)
        self.pnl_if_no = 0
        self.pnl_if_yes = 0
        self.event_id = event_id
        self.all_orders_df = None
        self.true_holdings = None
        self.unexecuted_value = None

    def _fetch_holdings_data(self):
        try:
            r = self.api_obj.tradex_caller("mybetsv2", body={"eventsStatus": "'A','F'"})
            mybets_df = pd.DataFrame(r["probes"])
            self.all_orders_df = pd.DataFrame(mybets_df.loc[mybets_df["id"] == self.event_id]["calls"].values[0])
        except IndexError:
            self.all_orders_df = pd.DataFrame()
            print("Zero holdings in event")
        except KeyError:
            self.all_orders_df = pd.DataFrame()
            print("Zero trades taken in event or zero holding in portfolio")

    def _set_unexecuted_value(self):
        if not self.all_orders_df.empty:
            mask_unmatched_buy = (self.all_orders_df["status"] == "A") & (self.all_orders_df["rank"] == -1)
            unexecuted_df = self.all_orders_df[mask_unmatched_buy]
            self.unexecuted_value = (unexecuted_df["coins"]*unexecuted_df["noofcontracts"]).sum()
        else:
            self.unexecuted_value = 0

    def _filter_true_holdings(self):
        if not self.all_orders_df.empty:
            mask_matched_buy = (self.all_orders_df["status"] == "A") & (self.all_orders_df["rank"] == 0)
            mask_unmatched_sell = (self.all_orders_df["status"] == "H")
            self.true_holdings = self.all_orders_df[mask_matched_buy | mask_unmatched_sell]
        else:
            self.true_holdings = pd.DataFrame()

    def calculate_pnl_df(self):
        if not self.true_holdings.empty:
            mask_asset_yes = self.true_holdings["callvalue"] == "Y"
            mask_asset_no = self.true_holdings["callvalue"] == "N"
            pnl_profit = (100 - self.true_holdings["coins"]) * self.true_holdings["noofcontracts"]
            pnl_loss = -1*self.true_holdings["coins"] * self.true_holdings["noofcontracts"]
            self.true_holdings["if_yes"] = np.where(mask_asset_yes, pnl_profit , pnl_loss)
            self.true_holdings["if_no"] = np.where(mask_asset_yes, pnl_loss, pnl_profit)



    def total_pnl_at_resolution(self):
        self._fetch_holdings_data()
        self._filter_true_holdings()
        # print(self.true_holdings)
        self.calculate_pnl_df()
        # print(self.true_holdings)
        self._set_unexecuted_value()
        if not self.true_holdings.empty:
            self.pnl_if_yes = self.true_holdings["if_yes"].sum()
            self.pnl_if_yes = np.round(self.pnl_if_yes,2)
            self.pnl_if_yes = float(self.pnl_if_yes)
            self.pnl_if_no = self.true_holdings["if_no"].sum()
            self.pnl_if_no = np.round(self.pnl_if_no, 2)
            self.pnl_if_no = float(self.pnl_if_no)



if __name__ == "__main__":
    # hpnl = HoldingPnl(11528)
    # hpnl.total_pnl_at_resolution()
    # print(hpnl.true_holdings)
    # print(hpnl.pnl_if_yes)
    # print(hpnl.pnl_if_no)

    # eid_list = [11427, 11426, 11425, 11424, 11423, 11422, 11421, 11420, 11419, 11418]
    #
    # for eid in eid_list:
    #     hpnl = HoldingPnl(eid)
    #     hpnl.total_pnl_at_resolution()
    #     print(eid, hpnl.pnl_if_yes, hpnl.pnl_if_no, hpnl.pnl_if_yes+ hpnl.pnl_if_no)

    r = tradex_caller("mybetsv2", body={"eventsStatus": "'A','F'"})
    print(r)
    print()
    mybets_df = pd.DataFrame(r["probes"])
    for i in mybets_df["id"]:
        orders_df = pd.DataFrame(mybets_df.loc[mybets_df["id"] == i]["calls"].values[0])

        print(orders_df)