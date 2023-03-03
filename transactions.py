from api_caller import ApiCaller
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')
import json
from statistics import mean
from transactions_cleaner import remove_cancelled_orders
from mybets import MyBets


class Transactions:
    def __init__(self, apitype=None, userid=None):
        # print("initialising Transactions")
        self.api_obj = ApiCaller(apitype, userid)
        self.mybet = MyBets(apitype, userid)

    def _get_transactions_df(self):
        """
        makes 'transactions' api call to tradex
        :return: dataframe containing passbook entries
        """
        resp1 = pd.DataFrame(self.api_obj.tradex_caller("transactions"))
        resp2 = pd.DataFrame(resp1["transactions"].to_list())
        return resp2


    def _rename_credits_by_tradex(self, df):
        """
        rename rfid and txnid transactions for given id for funds credited by tradex for market making to avoid null values in other columns
        :param df: dataframe containing passbook entry
        :return: dataframe with renamed entry for credits by tradex
        """
        df_temp = df.copy()
        # to_rename_id = [24686686, 29737283, 27188403, 33281495]
        # to_rename_id = [29737283, 27188403, 33281495]
        to_rename_id = [27188403, 33281495]
        df_temp = df_temp.set_index("id")
        for id in to_rename_id:
            df_temp["refid"].loc[id] = "tradex_credit_" + df_temp.loc[id]["createdat"]
            df_temp["txnid"].loc[id] = "tradex_credit000000"
        df_temp = df_temp.reset_index()
        return df_temp


    def _process_columns(self, df):
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


    def _expand_order_detail_col(self, df):
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


    def _expand_settled_or_closed_txn(self, df):
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


    def clean_transactions_df(self):
        """
        Makes 'transactions' Tradex API call and returns cleaned data
        :return: dataframe containing passbook entry with columns [date,createdat,event_id,refid,amount,order_detail,status,qty,asset,price]
        """
        df = self._get_transactions_df()
        # df = _rename_credits_by_tradex(df)
        df = self._process_columns(df)
        df = self._expand_order_detail_col(df)
        df = self._expand_settled_or_closed_txn(df)
        new_cols = ["date", "createdat", "event_id", "refid", "amount", "order_detail", "status", "qty", "asset", "price"]
        df = df[new_cols].copy()
        return df


    def get_event_transactions(self, event_id):
        """
        calls clean_transactions_df() and filters for provided event id
        :param event_id: Event id (int)
        :return: dataframe with only event transactions
        """
        df = self.clean_transactions_df()
        df2 = df[df["event_id"] == event_id]
        return df2


    def get_avg_buysell_price(self, event_id):
        # getting average sell prices for yes and no
        df = self.get_event_transactions(event_id)
        if not df.empty:
            mask_ys = (df["status"] == "Sold") & (df["asset"] == "Y")
            mask_ns = (df["status"] == "Sold") & (df["asset"] == "N")

            df_ys = df[mask_ys]
            df_ns = df[mask_ns]

            for df_temp in [df_ys, df_ns]:
                if not df_temp.empty:
                    df_temp["value"] = df_temp["price"] * df_temp["qty"]

            try:
                avgsellyes = df_ys["value"].sum() / df_ys["qty"].sum()
            except KeyError:
                avgsellyes = np.nan
            try:
                avgsellno = df_ns["value"].sum() / df_ns["qty"].sum()
            except KeyError:
                avgsellno = np.nan
        else:
            avgsellyes = np.nan
            avgsellno = np.nan

        # getting average buy prices from saved json from mybets/write_exec_buy_order(eid)
        # try:
        #     with open(f"buyprice_json/{event_id}.json", "r") as infile:
        #         prices = json.load(infile)
        # except FileNotFoundError:
        #     prices = {"yesbuy": [],
        #               "nobuy": []}
        # if len(prices["yesbuy"]) > 0:
        #     avgbuyyes = mean(prices["yesbuy"])
        # else:
        #     avgbuyyes = np.nan
        # if len(prices["nobuy"]) > 0:
        #     avgbuyno = mean(prices["nobuy"])
        # else:
        #     avgbuyno = np.nan

        """
        Below code temporarily commented to save time
        """
        # getting average buy prices from cleaned transactions data
        clean_df = remove_cancelled_orders(df)
        # cleaner_df = remove_unfilled_txn_qty(clean_df, event_id)

        mask_buy = clean_df["status"] == "Bought"

        remove_yes_qty, remove_yes_amount = self._get_unfilled_qty_n_amount(event_id, "Y")
        mask_yes = clean_df["asset"] == "Y"
        df_yesbuy = clean_df[mask_buy & mask_yes]
        avgbuyyes = ((df_yesbuy["price"] * df_yesbuy["qty"]).sum() - remove_yes_amount) / (
                    df_yesbuy["qty"].sum() - remove_yes_qty)

        remove_no_qty, remove_no_amount = self._get_unfilled_qty_n_amount(event_id, "N")
        mask_no = clean_df["asset"] == "N"
        df_nobuy = clean_df[mask_buy & mask_no]
        avgbuyno = ((df_nobuy["price"] * df_nobuy["qty"]).sum() - remove_no_amount) / (
                    df_nobuy["qty"].sum() - remove_no_qty)

        # for comparison with previous values
        mask_buy = clean_df["status"] == "Bought"

        mask_yes = clean_df["asset"] == "Y"
        df_yesbuy = clean_df[mask_buy & mask_yes]
        avgbuyyesfalse = (df_yesbuy["price"] * df_yesbuy["qty"]).sum() / df_yesbuy["qty"].sum()

        mask_no = clean_df["asset"] == "N"
        df_nobuy = clean_df[mask_buy & mask_no]
        avgbuynofalse = (df_nobuy["price"] * df_nobuy["qty"]).sum() / df_nobuy["qty"].sum()
        # avgbuyyes, avgsellyes, avgbuyno, avgbuyyesfalse, avgbuynofalse = 0,0,0,0,0

        return avgbuyyes, avgsellyes, avgbuyno, avgsellno, avgbuyyesfalse, avgbuynofalse


    def remove_unfilled_txn_qty(self, clean_txn_df, eid):
        """
        :param clean_txn_df:
        :param eid:
        :param df: would contain all transactions df
        :return: df with removed unfilled qty from txn df row
        """
        bets_df = self.mybet.get_event_holdings(eid)
        liveoid_info_list = []
        if not bets_df.empty:
            for oid in bets_df["orderid"].unique():
                oid_mask = bets_df["orderid"] == oid
                buy_mask = bets_df["side"] == "buy"
                temp = bets_df[oid_mask & buy_mask]
                print("MYBETS bought and oid unique")
                # print(temp)
                fill_df = temp[temp["status"] == "executed"]
                print("EXECUTED df")
                # print(fill_df)
                fqty = fill_df["qty"].sum()
                unfill_df = temp[temp["status"] == "pending"]
                print("PENDING df")
                # print(unfill_df)
                unfqty = unfill_df["qty"].sum()

                info_dict = {}
                info_dict["oid"] = oid
                info_dict["filledqty"] = fqty
                info_dict["unfilledqty"] = unfqty
                liveoid_info_list.append(info_dict)

        # print("mybets buy info: ", liveoid_info_list)
        clean_txn_df_copy = clean_txn_df.copy()
        for item in liveoid_info_list:
            temp2_df = clean_txn_df[clean_txn_df["refid"] == item["oid"]]
            print("OLD TRANSACTIONS for oid")
            # print(temp2_df)
            print("above shape: ", temp2_df.shape)
            if temp2_df.shape[0] == 1:
                print("Entered if statement temp2_df.shape[0] == 1")
                df_index = temp2_df.index.values[0]
                print("index fethced: ", df_index)
                # print(clean_txn_df_copy.head())
                # print(clean_txn_df_copy.loc[df_index])
                # print(clean_txn_df_copy.loc[df_index])
                (clean_txn_df_copy.loc[df_index, ["qty"]]) = item["filledqty"]
                # print("qty original:", (clean_txn_df_copy.loc[df_index]["qty"]), "qty new:", item["filledqty"])
                (clean_txn_df_copy.loc[df_index, ["amount"]]) = (clean_txn_df.loc[df_index]["price"]) * (
                clean_txn_df.loc[df_index]["qty"])
                # print("amount set ", "og amount:", (clean_txn_df_copy.loc[df_index]["amount"]), "new amount: ",
                #       (clean_txn_df.loc[df_index]["price"]) * (clean_txn_df.loc[df_index]["qty"]))
                # print("NEW TRANSACTIONS for oid")
                # print(clean_txn_df_copy[clean_txn_df_copy["refid"] == item["oid"]])
            else:
                print("more than 1 order id row")
        return clean_txn_df_copy


    def _get_unfilled_qty_n_amount(self, eid, asset):
        bets_df = self.mybet.get_event_holdings(eid)
        if not bets_df.empty:
            asset_mask = bets_df["asset"] == asset
            buy_mask = bets_df["side"] == "buy"
            status_mask = bets_df["status"] == "pending"
            new_bets = bets_df[asset_mask & buy_mask & status_mask]
            qty = new_bets["qty"].sum()
            amount = (new_bets["qty"] * new_bets["price"]).sum()
            return qty, amount
        else:
            return 0, 0


if __name__ == "__main__":
    # t = get_event_transactions(11985)
    # print(t)
    # print(t.columns)
    # t2 = t[["refid", "amount", "status", "qty", "asset", "price", "order_detail"]]
    # print(t2)
    # print(get_avg_buysell_price(6969))
    # t3 = t2[t2["status"] == "Bought"]
    # print(t3)
    # print("Avg buy price: ",t3["price"].mean())
    # t4 = t2[t2["status"] == "Sold"]
    # print(t4)
    # print("Avg sell price: ",t4["price"].mean())

    # eids = [11926,11927,11928,11929]
    # for id in eids:
    #     t = get_event_transactions(id)
    #     print("eid:",id)
    #     # print(t)
    #     # print(t.columns)
    #     t2 = t[["amount", "status", "qty", "asset", "price"]]
    #     # print(t2)
    #     t3 = t2[(t2["status"] == "Bought") & (t2["asset"] == "Y")]
    #     t3["value"] = t3["price"]*t3["qty"]
    #     # print(t3)
    #     print("Avg buy price yes: ", t3["value"].sum()/t3["qty"].sum())
    #     t4 = t2[(t2["status"] == "Sold") & (t2["asset"] == "Y")]
    #     t4["value"] = t4["price"] * t4["qty"]
    #     # print(t4)
    #     print("Avg sell price yes: ", t4["value"].sum()/t4["qty"].sum())
    #
    #     t5 = t2[(t2["status"] == "Bought") & (t2["asset"] == "N")]
    #     t5["value"] = t5["price"]*t5["qty"]
    #     # print(t5)
    #     print("Avg buy price no: ", t5["value"].sum()/t5["qty"].sum())
    #     t6 = t2[(t2["status"] == "Sold") & (t2["asset"] == "N")]
    #     t6["value"] = t6["price"]*t6["qty"]
    #     # print(t6)
    #     print("Avg sell price no: ", t6["value"].sum()/t6["qty"].sum())
    # df = get_event_transactions(12401)
    # print(df)
    # clean_df = remove_cancelled_orders(df)
    # print(clean_df)
    # cleaner_df = remove_unfilled_txn_qty(clean_df, 12401)
    # print(cleaner_df)
    obj = Transactions(apitype='p', userid=0)
    df = obj.get_event_transactions(12023)
    print(df.columns)
    print(df)
    print("total: ",df["amount"].sum())
