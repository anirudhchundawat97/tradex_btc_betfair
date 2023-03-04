from api_caller import ApiCaller
import pandas as pd
import numpy as np
import warnings
pd.options.display.max_columns = 50

import warnings
warnings.filterwarnings("ignore")

def _process_columns(df):
    """
    create columns with more details from data available
    :param df: dataframe containing passbook entry
    :return: dataframe with edited columns event_id, order_detail, date and amount
    """
    df_temp = df.copy()
    df_temp["event_id"] = df_temp["txnid"].str[-5:].astype(int)
    df_temp["order_detail"] = (df["message"].str.split(r"\n", expand=True))[1]
    df_temp["createdat"] = pd.to_datetime(df_temp['createdat'], infer_datetime_format=True)
    df_temp['createdat'] = df_temp['createdat'].dt.tz_convert('Asia/Kolkata')
    df_temp["date"] = df_temp['createdat'].dt.date
    df_temp["amount"] = np.where(df_temp["type"] == "CREDIT", df_temp["amount"], -1 * df_temp["amount"])
    return df_temp


def _expand_settled_or_closed_txn(df):
    """
    Updates status for trades with settled/closed message which couldn't be extracted using regex
    :param df: dataframe containing passbook entry with column 'order_detail'
    :return: dataframe containing passbook entry with column 'order_detail' expanded to status,qty,asset,price
    """
    df_temp = df.copy()
    df_temp = df_temp.set_index("id")
    for id in df_temp.index:
        if df_temp["order_detail"].loc[id] == None:
            pass
        elif "Settled" in df_temp["order_detail"].loc[id]:
            df_temp["status"].loc[id] = "Settled"
        elif "Closed" in df_temp["order_detail"].loc[id]:
            df_temp["status"].loc[id] = "Closed"
    df_temp.reset_index(inplace=True)
    return df_temp

def _expand_order_detail_col(df):
    """
    use regex to extract order detail from message
    :param df: dataframe containing passbook entry with column 'order_detail'
    :return: dataframe containing passbook entry with column 'order_detail' expanded to status,qty,asset,price
    """
    df_temp = df.copy()
    reg_ex = r"(Sold|Bought|Cancelled|Settled|Closed)\s([0-9.]+)\sshares\sx\s(YES|NO|Y|N)\s\(Rs\.\s([0-9.]+)\seach\)"
    df_temp["status"] = (df_temp["order_detail"].str.extract(reg_ex, expand=False))[0]
    df_temp["qty"] = (df_temp["order_detail"].str.extract(reg_ex, expand=False))[1].astype(float)
    df_temp["asset"] = (df_temp["order_detail"].str.extract(reg_ex, expand=False))[2]
    df_temp["price"] = (df_temp["order_detail"].str.extract(reg_ex, expand=False))[3].astype(float)
    return df_temp


class Transactions:
    def __init__(self, event_id, apitype=None, userid=None):
        self.api_obj = ApiCaller(apitype, userid)
        self.event_id = event_id
        self.all_txn_df = None
        self.event_txn_df = None
        self.yes_net_sold_value = None
        self.no_net_sold_value = None
        self.yes_net_buy_qty = None
        self.no_net_buy_qty = None
        self.settled_credit = False
        self.closed_credit = False

    def get_transactions(self):
        r = self.api_obj.tradex_caller("transactions")
        self.all_txn_df = pd.DataFrame(r["transactions"])
        df = self.all_txn_df
        df = _process_columns(df)
        df = df[df["event_id"] == self.event_id].copy()
        df = _expand_order_detail_col(df)
        df = _expand_settled_or_closed_txn(df)
        new_cols = ["date", "createdat", "event_id", "refid", "amount", "order_detail", "status", "qty", "asset",
                    "price"]
        self.event_txn_df = df[new_cols].copy()

    def get_bought_value(self):
        yes_df = self.event_txn_df[self.event_txn_df["asset"] == "Y"]
        self.yes_net_sold_value = yes_df["amount"].sum()
        no_df = self.event_txn_df[self.event_txn_df["asset"] == "N"]
        self.no_net_sold_value = no_df["amount"].sum()

    def get_settle_credit_if_any(self):
        if "Setlled" in self.event_txn_df["status"].values:
            self.settled_credit = True
        else:
            self.settled_credit = False
        if "Closed" in self.event_txn_df["status"].values:
            self.closed_credit = True
        else:
            self.closed_credit = False

    def set_qty_traded(self):
        df = self.event_txn_df.copy()
        df["buy_qty"] = 0
        mask_buy = df["status"] == "Bought"
        mask_sell = df["status"] == "Sold"
        mask_cancel = df["status"] == "Cancelled"
        df["buy_qty"] = np.where(mask_buy, df["qty"],
                                 np.where(mask_sell, -1 * df["qty"], np.where(mask_cancel, -1 * df["qty"], 0)))
        self.yes_net_buy_qty = df[df["asset"] == "Y"]["buy_qty"].sum()
        self.no_net_buy_qty = df[df["asset"] == "N"]["buy_qty"].sum()

    def update(self):
        try:
            self.get_transactions()
            self.get_bought_value()
            self.get_settle_credit_if_any()
            self.set_qty_traded()
        except Exception as e:
            raise Exception(e)

if __name__ == "__main__":
    from time import sleep
    while True:
        for eid in [24798, 24800, 24802, 24803, 24804]:
            tx = Transactions(eid, "p", 603727)
            tx.update()
            # sleep(5)
            # print(tx.event_txn_df)
            print(eid, "-"*10)
            print(eid," amount sum" ,tx.event_txn_df["amount"].sum())
            print(eid," yes bought qty", tx.yes_net_buy_qty)
            print(eid," no bought qty", tx.no_net_buy_qty)
            print(eid," settled", tx.settled_credit)
            print()
        break
    # eid = 24545
    # tx = Transactions(eid, "p", 603727)
    # tx.update()
    # sleep(5)
    # tx.event_txn_df["price+5"] = tx.event_txn_df["price"] + 5
    # # tx.event_txn_df["price+5"] = 100 - tx.event_txn_df["price"] + 10
    # print(tx.event_txn_df[["createdat", "status", "qty", "asset", "price", "price+5"]])
    # print(eid," amount sum" ,tx.event_txn_df["amount"].sum())
    # print(eid," yes bought qty", tx.yes_net_buy_qty)
    # print(eid," no bought qty", tx.no_net_buy_qty)
    # print(eid," settled", tx.settled_credit)
    # # pd.to_csv()




