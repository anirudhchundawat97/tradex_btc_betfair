from api_caller import tradex_caller
import pandas as pd
import numpy as np


def _get_lastTradesInfo_df(id):
    resp = tradex_caller("lastTradesInfo", body={"probeid": id})
    df = pd.DataFrame(resp["trades"])
    return df


def _sort_by_time(df):
    df["updatedat"] = pd.to_datetime(df['updatedat'], infer_datetime_format=True)
    df['updatedat'] = df['updatedat'].dt.tz_convert('Asia/Kolkata')
    df = df.sort_values(by="updatedat")
    df.reset_index(inplace=True)
    return df


def _remap_names(df):
    buy_as_a = df["status"] == "A"
    sell_as_ex = df["status"] == "EX"
    df["status"] = np.where(buy_as_a, "buy", np.where(sell_as_ex, "sell", None))
    col_rename_map = {'callvalue': 'asset',
                      'coins': 'price',
                      'noofcontracts': 'qty',
                      'status': 'side'}
    df.rename(columns=col_rename_map, inplace=True)
    return df


def clean_lastTradesInfo_df(id):
    df = _get_lastTradesInfo_df(id)
    df = _sort_by_time(df)
    df = _remap_names(df)
    return df


if __name__ == "__main__":
    print(clean_lastTradesInfo_df(9747))
