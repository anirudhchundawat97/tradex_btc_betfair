from api_caller import tradex_caller
from time import sleep
import pandas as pd

url_suffix = "lastTradesInfo"
eid = int(input("Enter event id:"))
body = {"probeid": eid}

while True:
    resp = tradex_caller(url_suffix, body)
    exec = pd.DataFrame(resp["trades"])
    yes_buy_df = exec[(exec["callvalue"] == "Y") & (exec["status"] == "A")]
    yes_sell_df = exec[(exec["callvalue"] == "Y") & (exec["status"] == "EX")]
    no_buy_df = exec[(exec["callvalue"] == "N") & (exec["status"] == "A")]
    no_sell_df = exec[(exec["callvalue"] == "N") & (exec["status"] == "EX")]

    yb_wap = (yes_buy_df["coins"] * yes_buy_df["noofcontracts"]).sum() / yes_buy_df["noofcontracts"].sum()
    ys_wap = (yes_sell_df["coins"] * yes_sell_df["noofcontracts"]).sum() / yes_sell_df["noofcontracts"].sum()
    nb_wap = (no_buy_df["coins"] * no_buy_df["noofcontracts"]).sum() / no_buy_df["noofcontracts"].sum()
    ns_wap = (no_sell_df["coins"] * no_sell_df["noofcontracts"]).sum() / no_sell_df["noofcontracts"].sum()

    print("YES BUY orders", "WAP: ", yb_wap)
    print(yes_buy_df)
    print("YES SELL orders", "WAP: ", ys_wap)
    print(yes_sell_df)
    print("NO BUY orders", "WAP: ", nb_wap)
    print(no_buy_df)
    print("NO SELL orders", "WAP: ", ns_wap)
    print(no_sell_df)
    print("-" * 80)

    sleep(15)
