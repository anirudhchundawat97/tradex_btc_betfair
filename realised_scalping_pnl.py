from api_caller import ApiCaller
import pandas as pd
import numpy as np
import datetime as dt
import warnings
from transactions import Transactions
from eda_event_trades import EdaEventTrades

warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", 500)
pd.set_option('display.expand_frame_repr', False)


class ScalpingPnl:
    def __init__(self, event_id, apitype='p', userid=603727):
        print(apitype, userid)
        self.apiobj = ApiCaller(apitype, userid)
        self.event_id = event_id
        self.orders_data = None
        self.orders_df = None
        self.yes_total_pnl = None
        self.no_total_pnl = None
        self.first_date = None
        self.yesqty = None
        self.noqty = None
        self.totalqty = None
        self.netpnl = None
        self.trans = Transactions(apitype, userid)
        self.edaeventradeObj = EdaEventTrades(self.event_id,generate_report=False, apitype=apitype, userid=userid)
        self.calculate_total_pnl()

    # def _fetch_transactions(self):
    #     r = tradex_caller("transactions")
    #     df = pd.DataFrame(r["transactions"])
    #     df["txnid"].loc[df["txnid"] == "CR10000ALGO"] = "CR10000ALGO-0000"
    #     return df
    #
    # def _extract_transactions_data(self, df):
    #     df["event_id"] = df["txnid"].str[-5:].astype(int)
    #     df["order_detail"] = (df["message"].str.split(r"\n", expand=True))[1]
    #     df["createdat"] = pd.to_datetime(df['createdat'], infer_datetime_format=True)
    #     df['createdat'] = df['createdat'].dt.tz_convert('Asia/Kolkata')
    #     df["date"] = df['createdat'].dt.date
    #
    #     reg_ex = r"(Sold|Bought|Cancelled|Settled|Closed)\s([0-9.]+)\sshares\sx\s(YES|NO|Y|N)\s\(Rs\.\s([0-9.]+)\seach\)"
    #
    #     df["side"] = (df["order_detail"].str.extract(reg_ex, expand=False))[0]
    #     df["qty"] = (df["order_detail"].str.extract(reg_ex, expand=False))[1].astype(float)
    #     df["asset"] = (df["order_detail"].str.extract(reg_ex, expand=False))[2]
    #     df["price"] = (df["order_detail"].str.extract(reg_ex, expand=False))[3].astype(float)
    #     return df
    #
    #
    # def _clean_transaction_data(self, df, event_id):
    #     df = df[df["event_id"] == event_id]
    #     col_rename_map = {'amount': 'from_wallet',
    #                       'refid': 'orderid'}
    #     df.rename(columns=col_rename_map, inplace=True)
    #     df["from_wallet"] = np.where(df["type"] == "CREDIT", df["from_wallet"], -1 * df["from_wallet"])
    #
    #     new_cols = ["date","createdat", "event_id", "orderid", "from_wallet", "side", "qty", "asset", "price"]
    #     df = df[new_cols].copy()
    #     return df

    def get_transactions(self):
        # raw_data = self._fetch_transactions()
        # txn_data = self._extract_transactions_data(raw_data)
        # self.orders_df = self._clean_transaction_data(txn_data, self.event_id)
        self.orders_df = self.trans.get_event_transactions(self.event_id)
        # self.trans.get_event_transactions(00)

    def calculate_total_pnl(self):
        self.get_transactions()
        yes_mask = (self.orders_df["asset"] == "Y") | (self.orders_df["asset"] == "YES")
        self.yes_total_pnl = (self.orders_df[yes_mask])["amount"].sum()
        self.yes_total_pnl = np.round(self.yes_total_pnl, 2)

        no_mask = (self.orders_df["asset"] == "N") | (self.orders_df["asset"] == "NO")
        self.no_total_pnl = (self.orders_df[no_mask])["amount"].sum()
        self.no_total_pnl = np.round(self.no_total_pnl, 2)

        self.netpnl = self.orders_df["amount"].sum()

    def calculate_daywise_pnl(self):
        grouped_df = self.orders_df.groupby(["date", "asset"])["amount"].sum()
        try:
            self.first_date = grouped_df.index[0][0]
        except:
            self.first_date = 0
        return grouped_df

    def get_true_qty_traded(self):
        self.edaeventradeObj.process_transactions(self.event_id)
        self.yesqty = (self.edaeventradeObj.df_yb["qty"].sum()) + (self.edaeventradeObj.df_ys["qty"].sum())
        self.noqty = (self.edaeventradeObj.df_nb["qty"].sum()) + (self.edaeventradeObj.df_ns["qty"].sum())
        self.totalqty = self.yesqty + self.noqty


if __name__ == "__main__":
    # spnl = ScalpingPnl(11418)
    # spnl.get_transactions()
    # print(spnl.orders_df)
    # print(spnl.calculate_total_pnl())
    # print()
    # grouped = spnl.calculate_daywise_pnl()
    # print(grouped)
    # print(grouped.index[0][0])
    # print(grouped[1])
    # print(spnl.yes_total_pnl)
    # print(spnl.no_total_pnl)
    eid_list = [11427, 11426, 11425, 11424, 11423, 11422, 11421, 11420, 11419, 11418]
    eid_list = [11855, 11856, 11857, 11858]
    eid_list = [11929, 11928, 11927, 11926]
    eid_list = [12098, 12099, 12100, 12101]

    for eid in eid_list:
        spnl = ScalpingPnl(eid)
        spnl.get_transactions()
        # spnl.get_true_qty_traded()
        grouped = spnl.calculate_daywise_pnl()
        print(eid, spnl.first_date, spnl.yes_total_pnl, spnl.no_total_pnl, spnl.yes_total_pnl + spnl.no_total_pnl)
        # print(spnl.totalqty, spnl.yesqty, spnl.noqty)
        print("net pnl", spnl.netpnl)
        # print(spnl.orders_df.columns)
        if ("Settled" in spnl.orders_df["status"].values):
            print("Settled")
        print(spnl.orders_df["status"].unique())
        if ("Closed" in spnl.orders_df["status"].values):
            print("Closed")
