import pandas as pd
import numpy as np
from api_caller import ApiCaller

class MyBets:
    def __init__(self, event_id, apitype=None, userid=None):
        self.api_obj = ApiCaller(apitype, userid)
        self.event_id = event_id
        self.portfolio_dict = None
        self.event_holdings_df = None
        self.holding_yes_qty = None
        self.holding_no_qty = None
        self.lastbuyprice_yes = None
        self.lastbuyprice_no = None
        self.lastsellprice_yes = None
        self.lastsellprice_no = None
        self.avgbuyprice_yes = None
        self.avgbuyprice_no = None
        self.avgsellprice_yes = None
        self.avgsellprice_no = None
        self.unmatched_buy_yes_value = None
        self.unmatched_buy_no_value = None

    def set_my_all_positions_dict(self):
        raw = self.api_obj.tradex_caller("mybetsv2", {"eventsStatus": "'A','F'"})
        positions_df = pd.DataFrame(raw["probes"])
        if not positions_df.empty:
            positions_df = positions_df.set_index("id")[["calls", 'summary']]
            self.portfolio_dict = positions_df.to_dict("index")
        else:
            self.portfolio_dict = {}

    def get_event_positions(self):
        try:
            event_holdings = self.portfolio_dict[self.event_id]["calls"]
        except KeyError:
            print(f"{self.event_id}: No event holdings")
            self.event_holdings_df = pd.DataFrame()
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
            event_holdings_df['buyprice'] = np.where(event_holdings_df['buyprice'] == 0, event_holdings_df['price'],
                                                     event_holdings_df['buyprice'])
            event_holdings_df['createdat'] = pd.to_datetime(event_holdings_df['createdat'])
            event_holdings_df['createdat'] = event_holdings_df['createdat'].dt.tz_convert('Asia/Kolkata')

            mask_executed_buy = (event_holdings_df['status'] == 'executed') & (event_holdings_df['side'] == 'buy')
            mask_pending_sell = (event_holdings_df['status'] == 'pending') & (event_holdings_df['side'] == 'sell')
            event_holdings_df['if_win_price'] = np.where(mask_executed_buy, 100 - event_holdings_df['price'], np.where(mask_pending_sell, 100 - event_holdings_df['price'], 0))

            event_holdings_df = event_holdings_df.sort_values(by="createdat", ascending=False)
            self.event_holdings_df = event_holdings_df.reset_index(drop=True)

    def get_holding_qty(self):
        df = self.event_holdings_df.copy()
        if not df.empty:
            mask_matched_buy = (df["side"] == "buy") & (df["status"] == "executed")
            mask_unmatched_sell = (df["side"] == "sell")
            true_holdings = df[mask_matched_buy | mask_unmatched_sell]
            mask_asset_yes = true_holdings["asset"] == "Y"
            yes_df = true_holdings[mask_asset_yes]
            if not yes_df.empty:
                self.holding_yes_qty = yes_df["qty"].sum()
            else:
                self.holding_yes_qty = 0

            mask_asset_no = true_holdings["asset"] == "N"
            no_df = true_holdings[mask_asset_no]
            if not no_df.empty:
                self.holding_no_qty = no_df["qty"].sum()
            else:
                self.holding_no_qty = 0
        else:
            self.holding_yes_qty = 0
            self.holding_no_qty = 0

    def get_lastbuy_price(self):
        df = self.event_holdings_df
        if not df.empty:
            mask_matched_buy = (df["side"] == "buy") & (df["status"] == "executed")
            mask_unmatched_sell = (df["side"] == "sell")
            true_holdings = df[mask_matched_buy | mask_unmatched_sell]

            mask_asset_yes = true_holdings["asset"] == "Y"
            yes_df = true_holdings[mask_asset_yes]
            if not yes_df.empty:
                self.lastbuyprice_yes = (yes_df["buyprice"]*yes_df["qty"]).sum() / yes_df["qty"].sum()
            else:
                self.lastbuyprice_yes = np.nan

            mask_asset_no = true_holdings["asset"] == "N"
            no_df = true_holdings[mask_asset_no]
            if not no_df.empty:
                self.lastbuyprice_no = (no_df["buyprice"]*no_df["qty"]).sum() / no_df["qty"].sum()
            else:
                self.lastbuyprice_no = np.nan
        else:
            self.lastbuyprice_yes = np.nan
            self.lastbuyprice_no = np.nan

    def get_avg_buysell_price(self):
        raw = self.api_obj.tradex_caller("mybets", {"eventid": self.event_id})
        # print(raw)
        if raw["probes"]:
            trades_df = pd.DataFrame(raw["probes"][0]["calls"])
            trades_df['createdat'] = pd.to_datetime(trades_df['createdat'])
            trades_df['createdat'] = trades_df['createdat'].dt.tz_convert('Asia/Kolkata')
            trades_df["remove_row"] = np.where((trades_df["rank"] == 0) & (trades_df["status"] == "A"), 1, 0)
            trades_df = trades_df[trades_df["remove_row"]==0].copy()
            mask_unbought = (trades_df["rank"] == -1) & (trades_df["status"] == "A")
            mask_cancelled = (trades_df["rank"] == 0) & (trades_df["status"] == "CN")
            trades_df["modified_qty"] = np.where(mask_unbought | mask_cancelled, -1 * trades_df["noofcontracts"], trades_df["noofcontracts"])
            grouped_df = trades_df.groupby(by="orderid")
            temp_df = grouped_df["modified_qty"].sum()

            final_df = pd.merge(trades_df, temp_df, left_on="orderid", right_on="orderid")
            final_df["value"] = final_df["coins"] * final_df["modified_qty_y"]

            yes_buy_orders_df = final_df[(final_df["status"]=="O") & (final_df["modified_qty_y"]!=0) & (final_df["callvalue"]=="Y")]
            no_buy_orders_df = final_df[(final_df["status"]=="O") & (final_df["modified_qty_y"]!=0) & (final_df["callvalue"]=="N")]
            yes_sell_orders_df = final_df[(final_df["status"] == "EX") & (final_df["callvalue"] == "Y")]
            no_sell_orders_df = final_df[(final_df["status"] == "EX") & (final_df["callvalue"] == "N")]

            self.avgbuyprice_yes = yes_buy_orders_df["value"].sum() / yes_buy_orders_df["modified_qty_y"].sum()
            self.avgbuyprice_no = no_buy_orders_df["value"].sum() / no_buy_orders_df["modified_qty_y"].sum()
            self.avgsellprice_yes = yes_sell_orders_df["value"].sum() / yes_sell_orders_df["modified_qty_y"].sum()
            self.avgsellprice_no = no_sell_orders_df["value"].sum() / no_sell_orders_df["modified_qty_y"].sum()

    def get_unmatched_value(self):
        df = self.event_holdings_df
        if not df.empty:
            mask_unmatched_buy = (df["side"] == "buy") & (df["status"] == "pending")
            unmatched_hold_df = df[mask_unmatched_buy]

            mask_asset_yes = unmatched_hold_df["asset"] == "Y"
            yes_df = unmatched_hold_df[mask_asset_yes]
            if not yes_df.empty:
                self.unmatched_buy_yes_value = (yes_df["qty"] * yes_df["price"]).sum()
            else:
                self.unmatched_buy_yes_value = 0

            mask_asset_no = unmatched_hold_df["asset"] == "N"
            no_df = unmatched_hold_df[mask_asset_no]
            if not no_df.empty:
                self.unmatched_buy_no_value = (no_df["qty"] * no_df["price"]).sum()
            else:
                self.unmatched_buy_no_value = 0
        else:
            self.unmatched_buy_yes_value = 0
            self.unmatched_buy_no_value = 0

    def update(self):
        self.set_my_all_positions_dict()
        self.get_event_positions()
        self.get_holding_qty()
        self.get_lastbuy_price()
        self.get_avg_buysell_price()
        self.get_unmatched_value()


if __name__ == "__main__":

    mb = MyBets(23782, "p", 603727)
    mb.update()
    # print(mb.portfolio_dict)
    # print(mb.)
    print(mb.event_holdings_df)
    print(mb.avgbuyprice_yes)
    print(mb.avgbuyprice_no)
    print(mb.avgsellprice_yes)
    print(mb.avgsellprice_no)

