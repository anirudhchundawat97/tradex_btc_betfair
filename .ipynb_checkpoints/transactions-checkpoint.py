from api_caller import tradex_caller
import pandas as pd
import numpy as np


def _get_transactions_df():
    """
    makes 'transactions' api call to tradex
    :return: dataframe containing passbook entries
    """
    resp1 = pd.DataFrame(tradex_caller("transactions"))
    resp2 = pd.DataFrame(resp1["transactions"].to_list())
    return resp2

def _rename_credits_by_tradex(df):
    """
    rename rfid and txnid transactions for given id for funds credited by tradex for market making to avoid null values in other columns
    :param df: dataframe containing passbook entry
    :return: dataframe with renamed entry for credits by tradex
    """
    df_temp = df.copy()
    to_rename_id = [24686686, 29737283, 27188403, 33281495]
    df_temp = df_temp.set_index("id")
    for id in to_rename_id:
        df_temp["refid"].loc[id] = "tradex_credit_"+df_temp.loc[id]["createdat"]
        df_temp["txnid"].loc[id] = "tradex_credit0000"
    df_temp = df_temp.reset_index()
    return df_temp

def _process_columns(df):
    """
    create columns with more details from data available
    :param df: dataframe containing passbook entry
    :return: dataframe with edited columns event_id, order_detail, date and amount
    """
    df_temp = df.copy()
    df_temp["event_id"] = df_temp["txnid"].str[-4:].astype(int)
    df_temp["order_detail"] = (df["message"].str.split(r"\n", expand=True))[1]
    df_temp["createdat"] = pd.to_datetime(df_temp['createdat'], infer_datetime_format=True)
    df_temp['createdat'] = df_temp['createdat'].dt.tz_convert('Asia/Kolkata')
    df_temp["date"] = df_temp['createdat'].dt.date
    df_temp["amount"] = np.where(df_temp["type"] == "CREDIT", df_temp["amount"], -1 * df_temp["amount"])
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

def clean_transactions_df():
    """
    Makes 'transactions' Tradex API call and returns cleaned data
    :return: dataframe containing passbook entry with columns [date,createdat,event_id,refid,amount,order_detail,status,qty,asset,price]
    """
    df = _get_transactions_df()
    df = _rename_credits_by_tradex(df)
    df = _process_columns(df)
    df = _expand_order_detail_col(df)
    df = _expand_settled_or_closed_txn(df)
    new_cols = ["date", "createdat", "event_id", "refid", "amount", "order_detail", "status", "qty", "asset", "price"]
    df = df[new_cols].copy()
    return df


if __name__ == "__main__":
    t = clean_transactions_df()
    print(t)
