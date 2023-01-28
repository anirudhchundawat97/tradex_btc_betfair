from event_params import EventParam
from time import sleep
import datetime as dt
import numpy as np

class PriceAttri(EventParam):
    def __init__(self, eid, apitype=None, userid=None):
        super().__init__(eid, apitype=apitype, userid=userid)
        # print("initialising Price Attributes")
        self.yes_tot_value = None
        self.yes_best_price = None
        self.yes_2ndbest_price = None
        self.yes_executed_wap = None
        self.yes_executed_avgpri = None
        self.yes_ob_vwap = None
        self.yes_value_per_pp = None

        self.no_tot_value = None
        self.no_best_price = None
        self.no_2ndbest_price = None
        self.no_executed_wap = None
        self.no_executed_avgpri = None
        self.no_ob_vwap = None
        self.no_value_per_pp = None

        self.avg_traded_qty = None

    def set_tot_pending_value(self):
        if not self.yes_pending_orders.empty:
            self.yes_tot_value = self.yes_pending_orders["value"].sum()
        if not self.no_pending_orders.empty:
            self.no_tot_value = self.no_pending_orders["value"].sum()

    def set_best_price(self):
        if not self.yes_pending_orders.empty:
            self.yes_best_price = self.yes_pending_orders["price"].iloc[0]
        else:
            # print(self.yes_pending_orders)
            self.yes_best_price = 0
        if self.yes_pending_orders.shape[0] > 1:
            self.yes_2ndbest_price = self.yes_pending_orders["price"].iloc[1]
        else:
            self.yes_2ndbest_price = np.nan
        if not self.no_pending_orders.empty:
            self.no_best_price = self.no_pending_orders["price"].iloc[0]
        else:
            # print(self.no_pending_orders)
            self.no_best_price = 0
        if self.no_pending_orders.shape[0] > 1:
            self.no_2ndbest_price = self.no_pending_orders["price"].iloc[1]
        else:
            self.no_2ndbest_price = np.nan

    def set_executed_wap_avgpri(self):
        self.yes_executed_wap, self.yes_executed_avgpri = self._calc_wap_avgpri("Y")
        self.no_executed_wap, self.no_executed_avgpri = self._calc_wap_avgpri("N")

    def set_ob_vwap(self):
        if not self.yes_pending_orders.empty:
            self.yes_ob_vwap = self.yes_pending_orders["value"].sum()/self.yes_pending_orders["qty"].sum()
        else:
            self.yes_ob_vwap = 0
        if not self.no_pending_orders.empty:
            self.no_ob_vwap = self.no_pending_orders["value"].sum()/self.no_pending_orders["qty"].sum()
        else:
            self.no_ob_vwap = 0


    def set_value_per_pp(self):
        if (self.yes_tot_value is not None) and (self.yes_best_price is not None):
            self.yes_value_per_pp = self.yes_tot_value / self.yes_best_price
        else:
            self.yes_value_per_pp = 0
        if (self.no_tot_value is not None) and (self.no_best_price is not None):
            self.no_value_per_pp = self.no_tot_value / self.no_best_price
        else:
            self.no_value_per_pp = 0

    def set_avg_qty_traded(self):
        if not self.last_executed_trades.empty:
            self.avg_traded_qty = self.last_executed_trades["qty"].mean()
        else:
            self.avg_traded_qty = 0

    def _calc_wap_avgpri(self, asset, avg_period=3):
        if not self.last_executed_trades.empty:
            temp_df = self.last_executed_trades.iloc[::-1].copy()
            try:
                mask_asset = temp_df["asset"] == asset
                df = temp_df[mask_asset].copy().reset_index()
            except:
                return 0, 0
            else:
                if not df.empty:
                    df["wap"] = None
                    df["value"] = df["price"] * df["qty"]
                    df["cumvalue"] = df["value"].cumsum()
                    df["price_ma"] = df["price"].rolling(avg_period).mean()
                    for i in df.index:
                        df.loc[i, "wap"] = df.loc[i, "cumvalue"] / df.loc[:i + 1, "qty"].sum()
                    df = df.fillna(0)
                    return df["wap"].iloc[-1], df["price_ma"].iloc[-1]
        else:
            return 0, 0

    def initialise_priceatri(self):
        self.initialise_event()
        self.set_tot_pending_value()
        self.set_best_price()
        # self.set_executed_wap_avgpri()
        self.set_ob_vwap()
        self.set_value_per_pp()
        self.set_avg_qty_traded()
        # print("-"*20,self.yes_best_price, self.yes_ob_vwap)

    def update_priceatri(self):
        self.update_event()
        self.set_tot_pending_value()
        self.set_best_price()
        # self.set_executed_wap_avgpri()
        self.set_ob_vwap()
        self.set_value_per_pp()
        self.set_avg_qty_traded()
        # print("-" * 20, self.no_best_price, self.no_ob_vwap)


if __name__ == "__main__":
    pa = PriceAttri(12461)
    print("-"*20, "class object created", "-"*20)
    print("title", pa.title)
    print("started_at", pa.started_at)
    print("ends_at", pa.ends_at)
    print("eid", pa.eid)
    print("yes_pending_orders", pa.yes_pending_orders)#.head(3))
    print("no_pending_orders", pa.no_pending_orders)#.head(3))
    print("last_executed_trades", pa.last_executed_trades)#.head(3))
    print()
    print("yes_tot_value", pa.yes_tot_value)
    print("yes_best_price", pa.yes_best_price)
    print("yes_executed_wap", pa.yes_executed_wap)
    print("yes_executed_avgpri", pa.yes_executed_avgpri)
    print("yes_value_per_pp", pa.yes_value_per_pp)

    print("no_tot_value", pa.no_tot_value)
    print("no_best_price", pa.no_best_price)
    print("no_executed_wap", pa.no_executed_wap)
    print("no_executed_avgpri", pa.no_executed_avgpri)
    print("no_value_per_pp", pa.no_value_per_pp)

    print("avg_traded_qty", pa.avg_traded_qty)
    print()
    pa.initialise_priceatri()
    print("-" * 20, "Price attribute intilised function", "-" * 20)
    print("title", pa.title)
    print("started_at", pa.started_at)
    print("ends_at", pa.ends_at)
    print("eid", pa.eid)
    print("yes_pending_orders", pa.yes_pending_orders.head(3))
    print("no_pending_orders", pa.no_pending_orders.head(3))
    print("last_executed_trades", pa.last_executed_trades.head(3))
    print()
    print("yes_tot_value", pa.yes_tot_value)
    print("yes_best_price", pa.yes_best_price)
    print("yes_executed_wap", pa.yes_executed_wap)
    print("yes_executed_avgpri", pa.yes_executed_avgpri)
    print("yes_value_per_pp", pa.yes_value_per_pp)

    print("no_tot_value", pa.no_tot_value)
    print("no_best_price", pa.no_best_price)
    print("no_executed_wap", pa.no_executed_wap)
    print("no_executed_avgpri", pa.no_executed_avgpri)
    print("no_value_per_pp", pa.no_value_per_pp)

    print("avg_traded_qty", pa.avg_traded_qty)
    print()
    while True:
        pa.update_priceatri()
        print("-" * 20, "Price attribute update function", "-" * 20)
        print("title", pa.title)
        print("started_at", pa.started_at)
        print("ends_at", pa.ends_at)
        print("eid", pa.eid)
        print("yes_pending_orders", pa.yes_pending_orders.head(3))
        print("no_pending_orders", pa.no_pending_orders.head(3))
        print("last_executed_trades", pa.last_executed_trades.head(3))
        print()
        print("yes_tot_value", pa.yes_tot_value)
        print("yes_best_price", pa.yes_best_price)
        print("yes_executed_wap", pa.yes_executed_wap)
        print("yes_executed_avgpri", pa.yes_executed_avgpri)
        print("yes_value_per_pp", pa.yes_value_per_pp)

        print("no_tot_value", pa.no_tot_value)
        print("no_best_price", pa.no_best_price)
        print("no_executed_wap", pa.no_executed_wap)
        print("no_executed_avgpri", pa.no_executed_avgpri)
        print("no_value_per_pp", pa.no_value_per_pp)

        print("avg_traded_qty", pa.avg_traded_qty)
        print()
        print()
        print("iso datetime endsat-",dt.datetime.fromisoformat(pa.ends_at))
        sleep(60)
